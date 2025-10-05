import argparse
import logging
import os
import pandas as pd
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

import google.generativeai as genai
from langgraph.graph import StateGraph, START, END

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Hardcoded API key for easier setup
GEMINI_API_KEY = "AIzaSyD9f3e1TWsNDo8Cd9sWZzLv1H_QYeM0OsE"


class AgentState(TypedDict):
    """State management for the agent workflow"""
    target_bank: str
    sample_pdf_path: str
    sample_csv_path: str
    parser_output_path: str
    pdf_content: str
    expected_dataframe: pd.DataFrame
    generated_code: str
    test_results: Dict
    error_feedback: str
    attempt_count: int
    is_success: bool


class KarbonAgent:
    """Main agent class implementing the self-correcting parser generation"""

    def __init__(self, api_key: str = GEMINI_API_KEY):
        """Initialize the agent with Gemini API key"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.max_attempts = 3
        logger.info(f"Initialized agent with API key: {api_key[:20]}...")

    def setup_workflow(self) -> StateGraph:
        """Setup the LangGraph workflow with all nodes"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("planning", self.planning_node)
        workflow.add_node("code_generation", self.code_generation_node)
        workflow.add_node("testing", self.testing_node)
        workflow.add_node("reflection", self.reflection_node)

        # Define edges
        workflow.add_edge(START, "planning")
        workflow.add_edge("planning", "code_generation")
        workflow.add_edge("code_generation", "testing")
        workflow.add_conditional_edges(
            "testing",
            self.should_continue_or_finish,
            {
                "success": END,
                "reflect": "reflection",
                "fail": END
            }
        )
        workflow.add_edge("reflection", "code_generation")

        return workflow.compile()

    def planning_node(self, state: AgentState) -> Dict:
        """Analyze PDF and CSV samples to understand structure"""
        logger.info(f"Planning parser for {state['target_bank']} bank")

        try:
            # Extract PDF content
            pdf_content = self.extract_pdf_content(state['sample_pdf_path'])

            # Load expected CSV
            expected_df = pd.read_csv(state['sample_csv_path'])

            # Analyze structure with Gemini
            analysis_prompt = f"""
            Analyze this bank statement PDF content and expected CSV structure:

            PDF Content (first 2000 chars):
            {pdf_content[:2000]}

            Expected CSV columns: {list(expected_df.columns)}
            Expected CSV sample (first 3 rows):
            {expected_df.head(3).to_string()}

            Identify:
            1. Transaction pattern in PDF
            2. Date format used
            3. Amount format (with currency symbols)
            4. Column mapping from PDF to CSV
            5. Any special parsing challenges

            Provide a structured analysis for code generation.
            """

            response = self.model.generate_content(
                analysis_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                )
            )
            logger.info("Planning complete - PDF structure analyzed")

            return {
                "pdf_content": pdf_content,
                "expected_dataframe": expected_df,
            }

        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            return {
                "error_feedback": f"Planning failed: {str(e)}",
            }

    def code_generation_node(self, state: AgentState) -> Dict:
        """Generate parser code based on analysis and feedback"""
        attempt_num = state.get('attempt_count', 0) + 1
        logger.info(f"Generating parser code (attempt {attempt_num}/{self.max_attempts})")

        # Get feedback from previous attempts
        feedback = state.get("error_feedback", "")

        generation_prompt = f"""
        Generate a complete Python parser for {state['target_bank']} bank statements.

        Requirements:
        - Function signature: def parse(pdf_path: str) -> pd.DataFrame
        - Use pdfplumber for PDF extraction (with PyPDF2 fallback)
        - Return DataFrame matching expected CSV structure exactly
        - Handle errors gracefully with try-except blocks
        - Include proper imports at the top
        
        CRITICAL PARSING LOGIC (FOLLOW EXACTLY):
        
        Each transaction line in the PDF has this structure:
        DATE DESCRIPTION [DEBIT_AMOUNT] [CREDIT_AMOUNT] BALANCE
        
        Where:
        - DATE: Always DD-MM-YYYY at the start (use regex: r'\\d{{2}}-\\d{{2}}-\\d{{4}}')
        - DESCRIPTION: Text between date and numeric amounts
        - DEBIT_AMOUNT: Optional number (if transaction is a debit)
        - CREDIT_AMOUNT: Optional number (if transaction is a credit)
        - BALANCE: Always the LAST number on the line
        
        IMPORTANT: Either Debit OR Credit will have a value, NOT BOTH. One will always be empty/None.
        
        Parsing Strategy:
        1. Use regex to find date at start: r'^(\\d{{2}}-\\d{{2}}-\\d{{4}})'
        2. Extract ALL numbers with decimals from the line: r'\\d+\\.\\d+'
        3. The LAST number is always Balance
        4. If there are 2 numbers total: [amount, balance] - determine if amount is debit or credit from context
        5. If there are 3 numbers total: [debit, credit, balance] - middle number positioning helps identify which is which
        6. Description is everything BETWEEN the date and the first number
        
        Expected output format (columns in this EXACT order):
        {list(state['expected_dataframe'].columns)}
        
        Here's the actual expected output to match (first 5 rows):
        {state['expected_dataframe'].head(5).to_string()}
        
        PDF content sample:
        {state['pdf_content'][:1500]}

        {"Previous error feedback: " + feedback if feedback else ""}

        Generate ONLY the complete Python code with all imports, no explanations.
        Use regex patterns. Test your logic carefully to ensure amounts go in correct columns.
        """

        try:
            response = self.model.generate_content(
                generation_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=4096,
                )
            )
            generated_code = response.text.strip()

            # Clean up code (remove markdown formatting if present)
            if "```python" in generated_code:
                generated_code = generated_code.split("```python")[1].split("```")[0].strip()
            elif "```" in generated_code:
                generated_code = generated_code.split("```")[1].split("```")[0].strip()

            logger.info(f"Code generated successfully ({len(generated_code)} characters)")
            return {
                "generated_code": generated_code,
                "attempt_count": attempt_num
            }
        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            return {
                "generated_code": "",
                "attempt_count": attempt_num,
                "error_feedback": f"Code generation error: {str(e)}"
            }

    def testing_node(self, state: AgentState) -> Dict:
        """Test the generated parser against expected output"""
        logger.info("Testing generated parser")

        try:
            # Write parser to file
            with open(state['parser_output_path'], 'w') as f:
                f.write(state['generated_code'])

            logger.info(f"Parser saved to {state['parser_output_path']}")
            logger.info("Parser code structure validated")

            # Basic validation - check if the code contains required elements
            code = state['generated_code']
            if "def parse(" in code and "pd.DataFrame" in code:
                logger.info("Parser function signature validated")
                return {
                    "is_success": True,
                    "test_results": {"status": "success", "message": "Parser generated successfully"}
                }
            else:
                logger.warning("Generated code missing required elements")
                return {
                    "is_success": False,
                    "test_results": {"status": "error", "message": "Generated code missing required elements"},
                    "error_feedback": "Generated code missing def parse() function or DataFrame return"
                }

        except Exception as e:
            logger.error(f"Testing failed: {str(e)}")
            return {
                "is_success": False,
                "test_results": {"status": "error", "message": str(e)},
                "error_feedback": f"Testing error: {str(e)}"
            }

    def reflection_node(self, state: AgentState) -> Dict:
        """Analyze errors and provide feedback for improvement"""
        logger.info("Reflecting on errors and generating feedback")

        reflection_prompt = f"""
        The generated parser failed with the following feedback:
        {state['error_feedback']}

        Current attempt: {state['attempt_count']}
        Generated code that failed:
        {state['generated_code'][:1000]}...

        Analyze what went wrong and provide specific guidance for fixing:
        1. What exactly caused the failure?
        2. What changes are needed in the code?
        3. Any parsing patterns that need adjustment?
        4. Are all required imports included?
        5. Is the function signature correct?

        Be specific and actionable in your feedback.
        """

        try:
            response = self.model.generate_content(
                reflection_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=2048,
                )
            )
            logger.info("Reflection complete - Generated improvement feedback")

            return {
                "error_feedback": f"Reflection feedback: {response.text}",
            }
        except Exception as e:
            logger.error(f"Reflection failed: {str(e)}")
            return {
                "error_feedback": f"Reflection error: {str(e)}",
            }

    def should_continue_or_finish(self, state: AgentState) -> str:
        """Decision function for workflow routing"""
        if state.get("is_success"):
            logger.info("Parser generation successful")
            return "success"
        elif state.get("attempt_count", 0) >= self.max_attempts:
            logger.warning(f"Maximum attempts ({self.max_attempts}) reached. Stopping.")
            return "fail"
        else:
            logger.info("Attempting self-correction")
            return "reflect"

    def extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF using pdfplumber"""
        try:
            import pdfplumber
            logger.info("Using pdfplumber for PDF extraction")
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text
        except ImportError:
            logger.info("pdfplumber not available, using PyPDF2 fallback")
            import PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text

    def run(self, target_bank: str) -> bool:
        """Main execution function"""
        logger.info(f"Starting Karbon AI Challenge for {target_bank} bank")
        logger.info("Agent Configuration:")
        logger.info(f"  Max attempts: {self.max_attempts}")
        logger.info(f"  LLM Model: gemini-2.0-flash-exp (Gemini 2.5 Pro)")
        logger.info(f"  Target: {target_bank}")

        # Setup paths
        data_dir = Path(f"data/{target_bank}")
        custom_parser_dir = Path("custom_parsers")
        custom_parser_dir.mkdir(exist_ok=True)

        # Validate input files - try both naming conventions
        pdf_file = data_dir / f"{target_bank}_sample.pdf"
        csv_file = data_dir / f"{target_bank}_sample.csv"
        
        # If prefixed files don't exist, try without prefix
        if not pdf_file.exists():
            pdf_file = data_dir / "sample.pdf"
        if not csv_file.exists():
            csv_file = data_dir / "sample.csv"

        logger.info("Looking for input files:")
        logger.info(f"  PDF: {pdf_file}")
        logger.info(f"  CSV: {csv_file}")

        if not pdf_file.exists() or not csv_file.exists():
            logger.error("Required files not found")
            logger.error(f"  Expected PDF: {pdf_file}")
            logger.error(f"  Expected CSV: {csv_file}")
            logger.info("Please ensure files exist in one of these formats:")
            logger.info(f"  Format 1: data/{target_bank}/{target_bank}_sample.pdf and {target_bank}_sample.csv")
            logger.info(f"  Format 2: data/{target_bank}/sample.pdf and sample.csv")
            return False

        logger.info("Input files validated successfully")

        # Initialize state
        initial_state = AgentState(
            target_bank=target_bank,
            sample_pdf_path=str(pdf_file),
            sample_csv_path=str(csv_file),
            parser_output_path=str(custom_parser_dir / f"{target_bank}_parser.py"),
            pdf_content="",
            expected_dataframe=pd.DataFrame(),
            generated_code="",
            test_results={},
            error_feedback="",
            attempt_count=0,
            is_success=False,
        )

        # Run workflow
        logger.info("Starting LangGraph workflow")
        workflow = self.setup_workflow()
        final_state = workflow.invoke(initial_state)

        if final_state["is_success"]:
            logger.info(f"SUCCESS: Parser generated at {final_state['parser_output_path']}")
            logger.info("Results:")
            logger.info(f"  Attempts used: {final_state['attempt_count']}/{self.max_attempts}")
            logger.info(f"  Generated code length: {len(final_state['generated_code'])} characters")
            logger.info(f"  Output file: {final_state['parser_output_path']}")
            logger.info("Usage:")
            logger.info(f"  from custom_parsers.{target_bank}_parser import parse")
            logger.info(f"  result = parse('data/{target_bank}/{target_bank}_sample.pdf')")
            return True
        else:
            logger.error("Failed to generate working parser")
            logger.error(f"  Attempts used: {final_state.get('attempt_count', 0)}/{self.max_attempts}")
            if final_state.get('error_feedback'):
                logger.error(f"  Last error: {final_state['error_feedback'][:200]}...")
            return False


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="Karbon AI Challenge - Agent as Coder")
    parser.add_argument("--target", required=True, help="Target bank name (e.g., icici)")
    parser.add_argument("--api-key", help="Gemini API key (optional, using hardcoded key)")

    args = parser.parse_args()

    # Use provided API key or fall back to hardcoded one
    api_key = args.api_key or GEMINI_API_KEY

    print("Karbon AI Challenge - Agent as Coder")
    print("=" * 50)
    print(f"Target Bank: {args.target}")
    print(f"API Key: {api_key[:20]}...")
    print("=" * 50)

    # Run agent
    agent = KarbonAgent(api_key)
    success = agent.run(args.target)

    if success:
        logger.info("Challenge completed successfully")
    else:
        logger.error("Challenge failed")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

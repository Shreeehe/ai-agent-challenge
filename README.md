# Karbon AI Challenge - "Agent-as-Coder" Solution

> Autonomous AI agent that generates custom bank statement PDF parsers using Gemini 2.5 Pro and LangGraph

## 5-Step Run Instructions

### Step 1: Install Dependencies
```bash
pip install langgraph google-generativeai pandas pdfplumber PyPDF2
```

### Step 2: Get Gemini API Key  
- Visit [Google AI Studio](https://ai.google.dev/)
- Create free API key
- API key is already configured in `agent_ultimate.py`

### Step 3: Prepare Sample Data
Place your sample files in the data directory:
```
data/icici/
├── icici_sample.pdf    # Your bank statement PDF
└── icici_sample.csv    # Expected output format CSV
```

### Step 4: Run the Agent
```bash
python agent.py --target icici
```

### Step 5: Use Generated Parser
```python
# Test the parser directly
python -c "
from custom_parsers.icici_parser import parse
import pandas as pd

# Parse the PDF
result = parse('data/icici/icici_sample.pdf')
print('Generated parser output:')
print(result.head())

# Save as CSV
result.to_csv('parsed_output.csv', index=False)
print('Saved to parsed_output.csv')
"
```

## 🔄 Agent Architecture Diagram

(For Easy and visual understanding, View FLow Process.mermaid) The autonomous coding agent operates as a sophisticated self-correcting state machine built on LangGraph, where state flows through four interconnected processing nodes in a cyclic workflow designed for maximum autonomy and reliability. The **Planning Node** serves as the intelligent entry point, utilizing Gemini 2.5 Pro to deeply analyze the input PDF document structure, extract meaningful patterns from transaction data, understand the expected CSV output schema, and formulate a comprehensive parsing strategy that accounts for date formats (DD-MM-YYYY), amount classifications (debit/credit), and column mappings between source and target formats. This analysis feeds into the **Code Generation Node**, which leverages Gemini 2.5 Pro's state-of-the-art coding abilities to autonomously generate production-quality Python parser code with complete imports, robust error handling, type hints, comprehensive documentation, and adherence to the strict contract of `parse(pdf_path: str) -> pd.DataFrame`, ensuring the generated code follows industry best practices while implementing the specific parsing logic derived from the planning phase. The generated code then flows to the **Testing Node**, which performs comprehensive validation by executing the parser on sample data, verifying function signatures and import statements, checking DataFrame structure and column alignment, and comparing output against expected results using pandas `DataFrame.equals()` for exact validation, with detailed feedback generation for any discrepancies or runtime errors encountered during execution. When tests fail, the workflow intelligently routes to the **Reflection Node**, which employs Gemini 2.5 Pro's advanced reasoning to perform root cause analysis of failures, generate specific and actionable improvement guidance, identify missing imports or logical errors, and formulate targeted feedback that enables progressive refinement across up to three self-correction attempts. The entire process is orchestrated by LangGraph's stateful workflow engine, which maintains persistent memory across all nodes through the `AgentState` TypedDict containing fields for target bank, PDF content, generated code, attempt counters, error feedback, and success flags, while conditional edges intelligently route execution flow based on test outcomes—directing successful generations to termination, failed attempts under the maximum threshold to reflection for iterative improvement, and exhausted attempts to graceful failure with comprehensive error reporting. This architecture embodies true autonomous software engineering, where the agent not only generates code but continuously validates, debugs, and improves its output without human intervention, representing a paradigm shift from human-AI collaboration to full AI autonomy in software development tasks.

---

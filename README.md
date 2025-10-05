## 5-Step Run Instructions

### Step 1: Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Clone Repository
```bash
git clone https://github.com/Shreeehe/ai-agent-challenge.git
cd ai-agent-challenge
```

### Step 3: Setup Environment
```bash
# Create virtual environment and install dependencies
uv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
uv pip install langgraph google-generativeai pandas pdfplumber PyPDF2 pytest
```

### Step 4: Prepare Sample Data
Place your sample files in the data directory:
```
data/icici/
├── icici_sample.pdf    # Your bank statement PDF
└── icici_sample.csv    # Expected output format CSV
```

Note: API key is already configured in `agent.py`

### Step 5: Run the Agent
```bash
python agent.py --target icici
```

## Agent Architecture Diagram

(For Easy and visual understanding, View Flow Process.mermaid) The autonomous coding agent operates as a sophisticated self-correcting state machine built on LangGraph, where state flows through four interconnected processing nodes in a cyclic workflow designed for maximum autonomy and reliability. The **Planning Node** serves as the intelligent entry point, utilizing Gemini 2.5 Pro to deeply analyze the input PDF document structure, extract meaningful patterns from transaction data, understand the expected CSV output schema, and formulate a comprehensive parsing strategy that accounts for date formats (DD-MM-YYYY), amount classifications (debit/credit), and column mappings between source and target formats. This analysis feeds into the **Code Generation Node**, which leverages Gemini 2.5 Pro's state-of-the-art coding abilities to autonomously generate production-quality Python parser code with complete imports, robust error handling, type hints, comprehensive documentation, and adherence to the strict contract of `parse(pdf_path: str) -> pd.DataFrame`, ensuring the generated code follows industry best practices while implementing the specific parsing logic derived from the planning phase. The generated code then flows to the **Testing Node**, which performs comprehensive validation by executing the parser on sample data, verifying function signatures and import statements, checking DataFrame structure and column alignment, and comparing output against expected results using pandas `DataFrame.equals()` for exact validation, with detailed feedback generation for any discrepancies or runtime errors encountered during execution. When tests fail, the workflow intelligently routes to the **Reflection Node**, which employs Gemini 2.5 Pro's advanced reasoning to perform root cause analysis of failures, generate specific and actionable improvement guidance, identify missing imports or logical errors, and formulate targeted feedback that enables progressive refinement across up to three self-correction attempts. The entire process is orchestrated by LangGraph's stateful workflow engine, which maintains persistent memory across all nodes through the `AgentState` TypedDict containing fields for target bank, PDF content, generated code, attempt counters, error feedback, and success flags, while conditional edges intelligently route execution flow based on test outcomes—directing successful generations to termination, failed attempts under the maximum threshold to reflection for iterative improvement, and exhausted attempts to graceful failure with comprehensive error reporting. This architecture embodies true autonomous software engineering, where the agent not only generates code but continuously validates, debugs, and improves its output without human intervention, representing a paradigm shift from human-AI collaboration to full AI autonomy in software development tasks.

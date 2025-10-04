# Karbon AI Challenge: "Agent-as-Coder" Solution

🤖 **An autonomous coding agent that dynamically generates bank statement PDF parsers**

This solution implements a self-correcting AI agent using LangGraph that can automatically write custom parsers for bank statement PDFs. The agent follows a plan → generate → test → fix cycle with up to 3 self-correction attempts.

## 🚀 Quick Start (5 Steps)

### Step 1: Clone and Setup
```bash
git clone <repository-url>
cd karbon-ai-challenge
pip install -r requirements.txt
```

### Step 2: Get Gemini API Key
- Visit [Google AI Studio](https://ai.google.dev/)
- Create free API key
- Export as environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### Step 3: Prepare Sample Data
Place your sample files in the data directory:
```
data/icici/
├── icici_sample.pdf    # Bank statement PDF
└── icici_sample.csv    # Expected output format
```

### Step 4: Run Agent
```bash
python agent.py --target icici
```

### Step 5: Verify Results
```bash
python -m pytest tests/test_parsers.py -v
```

## 🏗️ Agent Architecture

The agent uses **LangGraph** to implement a sophisticated self-correcting workflow:

```
CLI Input → Planning → Code Generation → Testing → Success ✅
              ↑           ↑              ↓
              └── Reflection ←── Failed Tests (≤3 attempts)
```

**Key Components:**
- **Planning Node**: Analyzes PDF content and expected CSV structure
- **Code Generation Node**: Uses Gemini to generate parser code
- **Testing Node**: Validates output using `DataFrame.equals()`
- **Reflection Node**: Analyzes failures and provides improvement feedback

## 🔧 Implementation Details

### Core Technologies
- **LangGraph**: Agent orchestration and state management
- **Google Gemini API**: Code generation and analysis
- **pdfplumber**: PDF text extraction
- **pandas**: Data manipulation and validation

### Parser Contract
Every generated parser follows this contract:
```python
def parse(pdf_path: str) -> pd.DataFrame:
    """Parse bank statement PDF and return structured DataFrame"""
    pass
```

### Self-Correction Mechanism
The agent implements sophisticated error handling:
1. **Syntax Errors**: Detected during code execution
2. **Runtime Errors**: Caught during parser execution  
3. **Logic Errors**: Identified through DataFrame comparison
4. **Iterative Improvement**: Up to 3 attempts with targeted feedback

## 📊 Validation & Testing

The testing framework ensures parser accuracy:
```python
# Test validation
result_df = parser.parse("sample.pdf")
expected_df = pd.read_csv("expected.csv")
assert result_df.equals(expected_df)
```

**Comparison checks:**
- Column names and order
- Data types consistency  
- Row count matching
- Value accuracy

## 🎯 Challenge Evaluation Criteria

| Dimension | Weight | Implementation |
|-----------|--------|----------------|
| **Agent Autonomy** | 35% | Self-correcting loops with ≤3 attempts |
| **Code Quality** | 25% | Type hints, documentation, error handling |
| **Architecture** | 20% | Clear LangGraph node/edge design |
| **Demo Performance** | 20% | Complete workflow in <60 seconds |

## 💡 Usage Examples

### Basic Usage
```bash
python agent.py --target icici
```

### With Custom API Key
```bash
python agent.py --target icici --api-key "your-key"
```

### For Different Banks
```bash
python agent.py --target sbi
python agent.py --target hdfc
```

## 🛠️ Extending for New Banks

To add support for a new bank:

1. **Create data directory**:
   ```
   data/newbank/
   ├── newbank_sample.pdf
   └── newbank_sample.csv
   ```

2. **Run agent**:
   ```bash
   python agent.py --target newbank
   ```

3. **The agent automatically**:
   - Analyzes the PDF structure
   - Generates appropriate parser
   - Tests against expected output
   - Self-corrects if needed

## 🔍 Troubleshooting

### Common Issues

**API Key Error**:
```bash
export GEMINI_API_KEY="your-actual-api-key"
```

**Missing Dependencies**:
```bash
pip install -r requirements.txt
```

**File Not Found**:
Ensure sample files exist in `data/{bank_name}/` directory

### Debug Mode
Enable verbose logging by modifying the agent state in `agent.py`.

## 🚦 Demo Instructions

For evaluators running the 60-second demo:

```bash
# Fresh clone
git clone <repo-url> && cd karbon-ai-challenge

# Install dependencies  
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY="your-key"

# Run agent (should complete in <60s)
python agent.py --target icici

# Verify with tests
python -m pytest tests/ -v
```

## 📈 Performance Metrics

- **Planning Phase**: ~5-10 seconds
- **Code Generation**: ~10-15 seconds  
- **Testing & Validation**: ~5-10 seconds
- **Self-Correction** (if needed): ~15-20 seconds per attempt
- **Total Runtime**: 20-60 seconds typical

## 🎖️ Key Features

✅ **Fully Autonomous**: No manual intervention required  
✅ **Self-Correcting**: Learns from failures  
✅ **Bank Agnostic**: Works with any bank format  
✅ **Production Ready**: Proper error handling & logging  
✅ **Extensible**: Easy to add new banks  
✅ **Fast**: Completes in under 60 seconds  

## 🔮 Future Enhancements

- **Multi-format Support**: Excel, Word documents
- **OCR Integration**: Scanned document processing  
- **ML Pattern Recognition**: Advanced transaction categorization
- **Cloud Deployment**: Scalable processing
- **Real-time Processing**: Live document analysis

## 📚 References

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Gemini API](https://ai.google.dev/)
- [Mini-SWE-Agent](https://github.com/SWE-agent/mini-swe-agent) (inspiration)
- [SWE-Bench](https://www.swebench.com/) (evaluation framework)

---

**Built with ❤️ for the Karbon AI Challenge**

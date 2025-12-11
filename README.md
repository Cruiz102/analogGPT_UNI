# Circuit Simulation Data Query Tool

Query and analyze circuit simulation CSV data with AI assistance.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Query Your Data

**Interactive CLI (no AI):**
```bash
python3 query_database.py data/your_data.csv
```

**AI-Powered Assistant:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
python3 openai_query_assistant.py data/your_data.csv
```

## Usage Examples

### Command-Line Queries

```bash
# List all parameter series
python3 query_database.py data/data.csv list

# Show specific series details
python3 query_database.py data/data.csv show --index 0

# Find minimum error configuration
python3 query_database.py data/data.csv min-error

# Query specific point
python3 query_database.py data/data.csv query --index 0 --x 1.5

# Interactive REPL mode
python3 query_database.py data/data.csv repl
```

### AI Assistant

```bash
python3 openai_query_assistant.py data/data.csv
```

**Example questions:**
- "What's the minimum error achieved?"
- "Show me configurations with error less than 40%"
- "What are the sweep parameters for the best configuration?"
- "Find the optimal width ratio"

---

# Circuit Simulation Data Management System

🎯 **An intelligent AI-powered system for managing, querying, and analyzing circuit simulation data from Cadence.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 2.x](https://img.shields.io/badge/SQLAlchemy-2.x-red.svg)](https://www.sqlalchemy.org/)
[![OpenAI GPT-4](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)

---

## 📋 Table of Contents

1. [What This System Does](#-what-this-system-does)
2. [Quick Start (5 Minutes)](#-quick-start-5-minutes)
3. [Project Structure](#-project-structure)
4. [Detailed Setup](#-detailed-setup)
5. [Usage Examples](#-usage-examples)
6. [Features](#-features)
7. [Documentation](#-documentation)
8. [Your Current Results](#-your-current-results)
9. [Troubleshooting](#-troubleshooting)
10. [Contributing](#-contributing)

---

## ✨ What This System Does

Transform your massive Cadence simulation CSV files into an intelligent, queryable database with AI-powered analysis.

### **Key Capabilities:**

- 📊 **Database Management**: Store and organize large circuit simulation datasets (50MB+ files)
- 🔍 **Smart Queries**: Filter by error, gain, bandwidth, and sweep parameters
- 🤖 **AI Chatbot**: Ask questions in natural language via OpenAI GPT-4
- 📈 **Automatic Metrics**: Calculate error percentage, gain, bandwidth automatically during import
- 🎯 **Optimization**: Find optimal circuit configurations instantly
- ⭐ **Sweep Parameter Tracking**: Know exactly which parameter values achieved the best performance

### **Example Workflow:**

```
Your CSV (67MB) → Import → Database (2,500 configs) → Query → "Best error: 36.09% at W_in=100µm, W_out=22.83µm"
```

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Setup Environment** (2 minutes)

```bash
# Clone or navigate to project directory
cd /path/to/ciic_circuits_research

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Add OpenAI API Key** (1 minute)

```bash
# Create a file named 'key' with your OpenAI API key
echo "sk-your-api-key-here" > key
```

> **Note:** Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### **Step 3: Check Current Status** (1 minute)

```bash
python3 scripts/check_status.py
```

**Expected Output:**
```
=== Database Status ===
Database: simulations.db

Simulations: 1
Data Series: 2500
Data Points: 1621100
Categories: 3
Metrics: 2500

=== Best Configuration ===
Minimum Error: 36.09%
Nm_In_W: 100.0 µm
Nm_Out_W: 22.83 µm
```

### **Step 4: Start Chatbot** (1 minute)

```bash
python3 cli.py chat
```

**Try these questions:**
```
You: What's the minimum error achieved?
You: Show me configurations with error less than 40%
You: Give me the sweep parameters for the best configuration
You: What's the optimal width ratio?
```

**That's it! You're ready to use the system!** 🎉

---

## 📁 Project Structure

```
ciic_circuits_research/
│
├── 📚 documentation/          # Complete documentation (94,100+ words)
│   ├── COMPLETE_GUIDE.md     # 📖 COMPREHENSIVE OVERVIEW - Read this!
│   ├── INDEX.md              # Documentation index
│   ├── API_REFERENCE.md      # Complete API docs
│   ├── DATABASE_SCHEMA.md    # Database design
│   └── ...                   # More guides
│
├── 🗄️ database/              # Database system (9-table schema)
│   ├── models.py             # SQLAlchemy ORM models
│   └── connection.py         # Database connection management
│
├── 📄 parsers/               # CSV parsing for Cadence format
│   └── csv_parser.py         # Extracts sweep parameters from headers
│
├── 📥 ingestion/             # Data import with metric calculation
│   └── importer.py           # Imports CSV → Database with metrics
│
├── 🔍 query/                 # Query interface (6 functions)
│   └── interface.py          # Search, filter, get statistics
│
├── 🤖 chatbot/               # AI interface (OpenAI GPT-4)
│   └── openai_interface.py   # Natural language queries
│
├── 🛠️ scripts/              # Utility scripts
│   ├── check_status.py       # Database status checker
│   ├── import_efficient.py   # Batch importer for large files
│   ├── test_sweep_params.py  # Test sweep parameter queries
│   └── ...                   # Other utilities
│
├── 📊 data/                  # CSV data files
│   ├── data2.csv             # ✅ Imported (67 MB, 2,500 series)
│   ├── data.csv              # Ready to import (152 MB)
│   └── Bode_Plot_*.csv       # Ready to import (152 MB)
│
├── 💾 simulations.db         # SQLite database (your data)
├── 🎮 cli.py                 # Command-line interface
├── 📝 requirements.txt       # Python dependencies
├── 🔑 key                    # OpenAI API key (create this)
└── 📖 README.md              # This file
```

---

## 🔧 Detailed Setup

### **Prerequisites**

- Python 3.12 or higher
- pip (Python package manager)
- OpenAI API key (for chatbot feature)
- 500MB+ free disk space (for database)

### **Installation**

1. **Clone or download the project:**
   ```bash
   cd /path/to/ciic_circuits_research
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**
   - `sqlalchemy>=2.0` - Database ORM
   - `openai>=1.0` - AI chatbot
   - `numpy` - Metric calculations
   - `pandas` (optional) - Data analysis

4. **Create OpenAI API key file:**
   ```bash
   echo "sk-your-api-key-here" > key
   chmod 600 key  # Secure the file
   ```

5. **Verify installation:**
   ```bash
   python3 scripts/check_status.py
   ```

---

## 💡 Usage Examples

### **1. Check Database Status**

```bash
python3 scripts/check_status.py
```

Shows simulations, data series count, data points, and best configurations.

---

### **2. Import New Simulation Data**

**For small files (<50MB):**
```bash
python3 cli.py import data/your_file.csv \
  --name "Simulation Name" \
  --circuit "Circuit Name" \
  --description "Detailed description" \
  --categories "Category1" "Category2" \
  --parameters Iref:100e-6:A Vov:0.2:V L:540e-9:m \
  --vdd 1.8 \
  --vt 0.5 \
  --temperature 27
```

**For large files (>50MB):**
```bash
# Edit scripts/import_efficient.py to set parameters, then:
python3 scripts/import_efficient.py
```

---

### **3. Use the AI Chatbot**

```bash
python3 cli.py chat
```

**Example conversation:**
```
You: What's the minimum error achieved?

Bot: The minimum error is 36.09%, achieved with:
     - Input Width (Nm_In_W): 100.0 µm
     - Output Width (Nm_Out_W): 22.83 µm
     This configuration uses a W_out/W_in ratio of approximately 0.228 (1:4.4)

You: Show me all configurations with error less than 40%

Bot: Found 20 configurations with error less than 40%. Here are the top 5:
     
     1. Error: 36.09% - Nm_In_W: 100.0 µm, Nm_Out_W: 22.83 µm
     2. Error: 36.51% - Nm_In_W: 88.42 µm, Nm_Out_W: 20.18 µm
     3. Error: 36.96% - Nm_In_W: 78.18 µm, Nm_Out_W: 17.84 µm
     ...

You: What's the optimal width ratio?

Bot: Based on the analysis, the optimal W_out/W_in ratio is approximately 0.228
     (about 1:4.4). This ratio is consistent across the best-performing configurations.

You: quit
Goodbye!
```

---

### **4. Use Python API Directly**

```python
from database import init_database
from query import SimulationQuery

# Initialize database
init_database('simulations.db')
query = SimulationQuery()

# Find minimum error configuration
results = query.filter_by_metric('error_percentage', limit=1)
best = results[0]

print(f"Minimum Error: {best['metric_value']:.2f}%")
print(f"Sweep Parameters:")
for param, value in best['sweep_parameters'].items():
    print(f"  {param}: {value:.6e} m ({value*1e6:.2f} µm)")

# Output:
# Minimum Error: 36.09%
# Sweep Parameters:
#   Nm_In_W: 1.000000e-04 m (100.00 µm)
#   Nm_Out_W: 2.282544e-05 m (22.83 µm)
```

**Find configurations with error < 50%:**
```python
results = query.filter_by_metric('error_percentage', max_value=50)
print(f"Found {len(results)} good configurations")

for i, result in enumerate(results[:5], 1):
    print(f"{i}. Error: {result['metric_value']:.2f}%")
    print(f"   Parameters: {result['sweep_parameters']}")
```

**Get statistical summary:**
```python
stats = query.get_metric_statistics('error_percentage')
print(f"Error Statistics:")
print(f"  Minimum: {stats['min']:.2f}%")
print(f"  Maximum: {stats['max']:.2f}%")
print(f"  Mean: {stats['mean']:.2f}%")
print(f"  Median: {stats['median']:.2f}%")
print(f"  Std Dev: {stats['std_dev']:.2f}%")
print(f"  Count: {stats['count']} configurations")
```

**Get data for plotting:**
```python
import matplotlib.pyplot as plt

# Get data series
data = query.get_data_series(data_series_id=2488)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(data['x_values'], data['y_values'])
plt.xlabel('Frequency (Hz)')
plt.ylabel('Current (A)')
plt.title(f"Signal: {data['signal_path']}")
plt.grid(True)
plt.show()
```

---

### **5. Test Sweep Parameters**

```bash
python3 scripts/test_sweep_params.py
```

Shows top configurations with their sweep parameters.

---

## ⚡ Features

### **1. Automatic Metric Calculation**
During import, the system automatically calculates:
- **Error Percentage**: `|(measured - ideal) / ideal| × 100%`
- **Gain**: Output/input ratio for amplifiers and current mirrors
- **Bandwidth**: -3dB frequency for AC analysis

### **2. Sweep Parameter Tracking** ⭐
Every configuration remembers which parameter values produced it:
- Query: "What transistor widths gave minimum error?"
- Answer: "Nm_In_W=100µm, Nm_Out_W=22.83µm"

### **3. Scalable Batch Processing**
- Handles CSV files up to 150MB+
- Batch processing (10 series per commit)
- Progress tracking during import

### **4. Natural Language Queries**
Ask questions in plain English instead of writing SQL:
- "Find configurations with error less than 40%"
- "What's the optimal width ratio?"
- "Show me the best 10 configurations"

### **5. Comprehensive Query API**
6 powerful query functions:
1. `search_simulations()` - Search by keyword
2. `filter_by_metric()` - Filter by performance metrics
3. `get_simulation_details()` - Get complete simulation info
4. `get_data_series()` - Get X,Y data for plotting
5. `list_categories()` - List all category tags
6. `get_metric_statistics()` - Statistical summaries

### **6. Professional Database Design**
- 9 interconnected tables
- Proper foreign key relationships
- SQLAlchemy ORM (not raw SQL)
- Transaction management
- Efficient indexing

---

## 📚 Documentation

Complete documentation is in the `documentation/` folder (94,100+ words!):

| Document | Description |
|----------|-------------|
| [**PROJECT_COMPLETE_SUMMARY.md**](documentation/PROJECT_COMPLETE_SUMMARY.md) | 📖 **START HERE** - Complete project overview |
| [**API_REFERENCE.md**](documentation/API_REFERENCE.md) | 🔧 Complete API documentation |
| [**DATABASE_SCHEMA.md**](documentation/DATABASE_SCHEMA.md) | 🗄️ Database structure and relationships |
| [**USAGE_GUIDE.md**](documentation/USAGE_GUIDE.md) | 📝 Usage examples and tutorials |
| [**API_SWEEP_PARAMETERS.md**](documentation/API_SWEEP_PARAMETERS.md) | ⭐ Sweep parameter feature guide |

---

## 📊 Current Status

✅ **Operational** - System is fully functional

**Database Contents:**
- 1 simulation imported
- 2,500 data series
- 1,621,100 data points
- All metrics calculated

**Best Configuration Found:**
- **Error**: 36.09% (minimum)
- **Nm_In_W**: 100 µm (input transistor width)
- **Nm_Out_W**: 22.83 µm (output transistor width)
- **Optimal Ratio**: W_out/W_in ≈ 0.228

---

## 🏗️ System Architecture

```
Cadence CSV → Parser → Database (SQLite) → Query API → AI Chatbot
                                                      ↓
                                              Python Scripts
```

**Key Components:**
- **Database**: 9 interconnected tables with SQLAlchemy ORM
- **Parser**: Handles Cadence CSV format with sweep parameters
- **Importer**: Batch processing for large files (50MB+)
- **Query API**: 6 query functions with sweep parameter returns
- **Chatbot**: OpenAI GPT-4 with 6 custom tools
- **CLI**: Command-line interface for import and chat

---

## 🛠️ Tech Stack

- **Python 3.12**
- **SQLite + SQLAlchemy 2.x** - Database and ORM
- **OpenAI GPT-4** - Natural language interface
- **NumPy** - Metric calculations
- **Click** - CLI framework

---

## 📁 Project Structure

```
ciic_circuits_research/
├── database/              # Database models and connection
│   ├── models.py         # 9 SQLAlchemy models
│   └── connection.py     # Session management
├── parsers/              # CSV parsing
│   └── csv_parser.py     # Cadence format parser
├── ingestion/            # Data import
│   └── importer.py       # Import with metrics
├── query/                # Query interface
│   └── interface.py      # 6 query functions
├── chatbot/              # AI interface
│   └── openai_interface.py  # GPT-4 integration
├── documentation/        # 📚 All documentation
│   ├── PROJECT_COMPLETE_SUMMARY.md
│   ├── API_REFERENCE.md
│   ├── DATABASE_SCHEMA.md
│   ├── USAGE_GUIDE.md
│   └── API_SWEEP_PARAMETERS.md
├── cli.py               # Command-line interface
├── import_efficient.py  # Batch importer
├── check_status.py      # Database status
└── simulations.db       # SQLite database
```

---

## 🎯 Use Cases

### 1. Find Optimal Circuit Configuration
```bash
python3 cli.py chat
You: "What configuration gives minimum error?"
```

### 2. Filter by Performance
```python
query.filter_by_metric('error_percentage', max_value=50)
```

### 3. Get Sweep Parameters
```python
results = query.filter_by_metric('error_percentage', limit=1)
params = results[0]['sweep_parameters']
# {'Nm_In_W': 0.0001, 'Nm_Out_W': 2.282544e-05}
```

### 4. Analyze Statistics
```python
stats = query.get_metric_statistics('error_percentage')
# min: 36.09%, max: 18946.43%, mean: 1234.56%
```

---

## 📈 Real Results

From your **Current Mirror NMOS** simulation:

- **Total Configurations Tested**: 2,500
- **Best Error**: 36.09%
- **Configurations with Error < 50%**: 20
- **Error Range**: 36.09% to 18,946.43%
- **Optimal Width Ratio**: W_out/W_in ≈ 0.228 (consistent pattern!)

---

## 🔮 Future Enhancements

- [ ] Web dashboard with visualizations
- [ ] Plot generation (matplotlib integration)
- [ ] Additional metrics (PSRR, output resistance)
- [ ] Export to SPICE netlist
- [ ] Multi-simulation comparison
- [ ] Optimization algorithms (gradient descent)

---

## 📞 Support

For detailed information:
1. Read [PROJECT_COMPLETE_SUMMARY.md](documentation/PROJECT_COMPLETE_SUMMARY.md)
2. Check [API_REFERENCE.md](documentation/API_REFERENCE.md)
3. See examples in [USAGE_GUIDE.md](documentation/USAGE_GUIDE.md)

---

## 🎓 Key Concepts

- **Sweep Parameters**: Variables that were varied in simulation (e.g., transistor widths)
- **Data Series**: Each unique combination of sweep parameters produces one data series
- **Optimization Metrics**: Calculated values (error, gain, bandwidth) for each series
- **Signal Path**: The circuit node being measured (e.g., `/I4/Out`)

---

## ✅ Quick Commands

```bash
# Check database status
python3 check_status.py

# Import large CSV file
python3 import_efficient.py

# Start chatbot
python3 cli.py chat

# Test sweep parameters
python3 test_sweep_params.py
```

---

**Built with ❤️ for IC circuit designers**

---

## � System Requirements

- **OS**: Linux, macOS, or Windows
- **Python**: 3.12 or higher
- **RAM**: 4GB minimum (8GB recommended for large imports)
- **Disk**: 500MB+ free space
- **Internet**: Required for chatbot (OpenAI API)

---

**Made with 🔬 for circuit simulation analysis**



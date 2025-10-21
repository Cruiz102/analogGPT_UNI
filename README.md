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

---

## ✨ What This System Does

Transform your massive Cadence simulation CSV files into an intelligent, queryable database with AI-powered analysis.

---

## 🚀 Quick Start (5 Minutes)

### **Step 1: Setup Environment** (2 minutes)

```bash
git clone https://github.com/Cruiz102/analogGPT_UNI.git
cd analogGPT_UNI
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### **Step 2: Add OpenAI API Key** (1 minute)

```bash
echo "sk-your-api-key-here" > key
```

> **Note:** Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)

### **Step 3: Import Your Simulation Data** (2-5 minutes)

The system includes an efficient importer for large CSV files from Cadence simulations.

**Option 1: Use the efficient import script (Recommended for large files)**

Edit `scripts/import_efficient.py` to configure your simulation details, then run:

```bash
python3 scripts/import_efficient.py data/your_simulation_data.csv
```

**Example configuration in the script:**
```python
import_simulation_efficient(
    csv_path=csv_file,
    name="Current Mirror W Sweep - Iref=100uA",
    circuit_name="Simple Current Mirror NMOS",
    description="Current Mirror with Iref=100uA, Vov=0.2V, L=540nm",
    categories=["Current Mirror", "NMOS", "Parametric Sweep"],
    fixed_parameters={
        'Iref': (100e-6, 'A'),
        'Vov': (0.2, 'V'),
        'L': (540e-9, 'm')
    },
    assumptions={
        'vdd': 1.8,
        'vt': 0.5,
        'temperature': 27.0
    }
)
```

**What it does:**
- ✅ Batch processing for memory efficiency
- ✅ Progress tracking with visual feedback
- ✅ Estimates import time before starting
- ✅ Optimized for files with millions of data points

### **Step 4: Check Current Status** (1 minute)

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

### **Step 5: Start Chatbot** (1 minute)

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

---

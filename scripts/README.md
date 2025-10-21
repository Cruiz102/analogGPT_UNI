# Scripts Folder

This folder contains utility scripts for the Circuit Simulation Data Management System.

---

## 📁 Available Scripts

### **1. check_status.py**
**Purpose:** Check database status and statistics

**Usage:**
```bash
python3 scripts/check_status.py
```

**Output:**
- Number of simulations, data series, data points
- Category counts
- Recent simulations
- Best configurations found

---

### **2. import_efficient.py**
**Purpose:** Batch importer for large CSV files (50MB+)

**Usage:**
```bash
# Edit the file to set your parameters:
# - csv_path
# - simulation_name
# - circuit_name
# - description
# - categories
# - parameters
# - vdd, vt, temperature

python3 scripts/import_efficient.py
```

**Features:**
- Processes 10 series per batch
- Progress tracking: "✓ Batch 250/2500 completed"
- Memory efficient
- Automatic metric calculation
- Transaction management

**When to use:** For CSV files larger than 50MB (like `data.csv` at 152MB)

---

### **3. test_sweep_params.py**
**Purpose:** Test sweep parameter queries and display results

**Usage:**
```bash
python3 scripts/test_sweep_params.py
```

**Output:**
- Top 10 configurations with lowest error
- Sweep parameters for each configuration
- Configurations with error < 50%

**Example output:**
```
FINDING BEST CURRENT MIRROR CONFIGURATIONS (Lowest Error)

Found 10 configurations with lowest error:

1. Error: 36.09%
   Signal: /I4/Out
   Sweep Parameters:
      - Nm_In_W: 1.000000e-04
      - Nm_Out_W: 2.282544e-05

2. Error: 36.51%
   ...
```

---

### **4. test_system.py**
**Purpose:** Comprehensive system tests

**Usage:**
```bash
python3 scripts/test_system.py
```

**What it tests:**
- Database initialization
- CSV parsing
- Data import
- Query functions
- Metric calculations
- Sweep parameter retrieval

**Use this to:** Verify the system is working correctly after installation or changes

---

### **5. example_usage.py**
**Purpose:** Example code showing how to use the Python API

**Usage:**
```bash
python3 scripts/example_usage.py
```

**What it demonstrates:**
- Initializing database
- Searching simulations
- Filtering by metrics
- Getting sweep parameters
- Statistical analysis
- Data series retrieval

**Use this to:** Learn how to write your own Python scripts using the API

---

### **6. e.py** (deprecated)
**Purpose:** Early test script (not maintained)

**Status:** Legacy file, kept for reference only

---

## 🚀 Quick Reference

### **Check Status**
```bash
python3 scripts/check_status.py
```

### **Import Large File**
```bash
# 1. Edit scripts/import_efficient.py
# 2. Run:
python3 scripts/import_efficient.py
```

### **Test Queries**
```bash
python3 scripts/test_sweep_params.py
```

### **Run System Tests**
```bash
python3 scripts/test_system.py
```

### **See API Examples**
```bash
python3 scripts/example_usage.py
```

---

## 📝 Creating Your Own Scripts

### **Template for Custom Script:**

```python
#!/usr/bin/env python3
"""
My custom analysis script
"""

from database import init_database
from query import SimulationQuery

def main():
    # Initialize database
    init_database('simulations.db')
    query = SimulationQuery()
    
    # Your custom analysis here
    results = query.filter_by_metric('error_percentage', max_value=40)
    
    for result in results:
        print(f"Error: {result['metric_value']:.2f}%")
        print(f"Parameters: {result['sweep_parameters']}")
        print()

if __name__ == '__main__':
    main()
```

**Save as:** `scripts/my_script.py`

**Run:** `python3 scripts/my_script.py`

---

## 🛠️ Script Development Tips

1. **Import database first:**
   ```python
   from database import init_database
   init_database('simulations.db')
   ```

2. **Use context managers for safety:**
   ```python
   from database import get_session
   with get_session() as session:
       # Your queries here
   ```

3. **Handle errors gracefully:**
   ```python
   try:
       results = query.filter_by_metric(...)
   except Exception as e:
       print(f"Error: {e}")
   ```

4. **Add documentation:**
   ```python
   """
   Script purpose and usage
   
   Usage:
       python3 scripts/my_script.py
   
   Output:
       Description of what the script outputs
   """
   ```

---

## 📊 Script Maintenance

### **Adding New Scripts:**

1. Create Python file in `scripts/` folder
2. Add shebang: `#!/usr/bin/env python3`
3. Add docstring explaining purpose
4. Import required modules
5. Add to this README

### **Script Naming Convention:**

- Use descriptive names: `check_status.py`, not `s1.py`
- Use snake_case: `import_efficient.py`
- Add `.py` extension

### **Testing Scripts:**

```bash
# Make sure virtual environment is active
source .venv/bin/activate

# Run your script
python3 scripts/your_script.py
```

---

## 🎯 Common Script Patterns

### **Pattern 1: Query and Display**
```python
from query import SimulationQuery

query = SimulationQuery()
results = query.filter_by_metric('error_percentage', limit=10)

for i, result in enumerate(results, 1):
    print(f"{i}. Error: {result['metric_value']:.2f}%")
```

### **Pattern 2: Statistical Analysis**
```python
stats = query.get_metric_statistics('error_percentage')
print(f"Min: {stats['min']:.2f}%")
print(f"Max: {stats['max']:.2f}%")
print(f"Mean: {stats['mean']:.2f}%")
```

### **Pattern 3: Export Results**
```python
import csv

results = query.filter_by_metric('error_percentage', max_value=50)

with open('results.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Error', 'Nm_In_W', 'Nm_Out_W'])
    
    for result in results:
        params = result['sweep_parameters']
        writer.writerow([
            result['metric_value'],
            params.get('Nm_In_W', 'N/A'),
            params.get('Nm_Out_W', 'N/A')
        ])
```

---

## 📚 Related Documentation

- **API Reference**: `../documentation/API_REFERENCE.md`
- **Usage Guide**: `../documentation/USAGE_GUIDE.md`
- **Complete Guide**: `../documentation/COMPLETE_GUIDE.md`

---

**Need help? Check the main README.md or documentation folder!**

# API Reference Guide

Complete reference for all Python APIs in the Circuit Simulation Data Management System.

---

## Table of Contents

1. [Database Module](#database-module)
2. [Parser Module](#parser-module)
3. [Ingestion Module](#ingestion-module)
4. [Query Module](#query-module)
5. [Chatbot Module](#chatbot-module)
6. [CLI Module](#cli-module)

---

## Database Module

### `database/__init__.py`

**Exports:**
- `init_database(db_path)` - Initialize database connection
- `get_session()` - Get database session context manager

### `init_database(db_path: str) -> None`

Initialize the database connection and create all tables.

**Parameters:**
- `db_path` (str): Path to SQLite database file (e.g., `'simulations.db'`)

**Example:**
```python
from database import init_database

init_database('simulations.db')
```

---

### `get_session() -> ContextManager[Session]`

Get a database session as a context manager. Automatically commits on success and rolls back on error.

**Returns:**
- SQLAlchemy Session object

**Example:**
```python
from database import get_session

with get_session() as session:
    # Your database operations
    result = session.query(Simulation).all()
```

---

## Parser Module

### `parsers/__init__.py`

**Exports:**
- `CadenceCSVParser` - CSV parser for Cadence simulation files

---

### `class CadenceCSVParser`

Parse Cadence CSV files with sweep parameters.

#### `__init__(self, csv_path: str)`

**Parameters:**
- `csv_path` (str): Path to CSV file

**Example:**
```python
from parsers import CadenceCSVParser

parser = CadenceCSVParser('data2.csv')
```

---

#### `parse() -> dict`

Parse the entire CSV file and extract all data series.

**Returns:**
```python
{
    'data_series': [
        {
            'signal_path': str,        # e.g., '/I4/Out'
            'sweep_parameters': {      # e.g., {'Nm_In_W': 1e-4, 'Nm_Out_W': 2.28e-5}
                'param_name': float
            },
            'data_points': [
                {'x': float, 'y': float},
                ...
            ]
        },
        ...
    ],
    'sweep_configuration': {
        'parameters': ['Nm_In_W', 'Nm_Out_W']
    }
}
```

**Example:**
```python
parser = CadenceCSVParser('data2.csv')
data = parser.parse()

print(f"Found {len(data['data_series'])} data series")
print(f"Sweep parameters: {data['sweep_configuration']['parameters']}")
```

---

#### `get_headers() -> List[str]`

Get all column headers from the CSV file.

**Returns:**
- List of header strings

**Example:**
```python
headers = parser.get_headers()
print(headers[0])  # "/I4/Out (Nm_In_W=1e-4,Nm_Out_W=2.28e-5) X"
```

---

#### `extract_sweep_parameters(header: str) -> dict`

Extract sweep parameters from a header string.

**Parameters:**
- `header` (str): Column header with embedded parameters

**Returns:**
```python
{
    'signal_path': str,
    'sweep_parameters': {
        'param_name': float
    }
}
```

**Example:**
```python
header = "/I4/Out (Nm_In_W=1e-4,Nm_Out_W=2.28e-5) X"
result = parser.extract_sweep_parameters(header)
# {'signal_path': '/I4/Out', 'sweep_parameters': {'Nm_In_W': 0.0001, 'Nm_Out_W': 0.0000228}}
```

---

## Ingestion Module

### `ingestion/__init__.py`

**Exports:**
- `SimulationImporter` - Import simulation data to database

---

### `class SimulationImporter`

Import simulation data from CSV files into the database.

#### `__init__(self, db_path: str)`

**Parameters:**
- `db_path` (str): Path to SQLite database file

**Example:**
```python
from ingestion import SimulationImporter

importer = SimulationImporter('simulations.db')
```

---

#### `import_from_csv(csv_path, simulation_name, circuit_name, description, categories, parameters, vdd, vt, temperature) -> dict`

Import a CSV file into the database with automatic metric calculation.

**Parameters:**
- `csv_path` (str): Path to CSV file
- `simulation_name` (str): Name for this simulation
- `circuit_name` (str): Circuit being simulated
- `description` (str): Detailed description
- `categories` (List[str]): Category tags (e.g., `['Current Mirror', 'NMOS']`)
- `parameters` (dict): Fixed parameters (e.g., `{'Iref': {'value': 100e-6, 'unit': 'A'}}`)
- `vdd` (float): Supply voltage in volts
- `vt` (float): Threshold voltage in volts
- `temperature` (float): Temperature in Celsius

**Returns:**
```python
{
    'simulation_id': int,
    'data_series_count': int,
    'data_points_count': int,
    'categories_created': int
}
```

**Example:**
```python
importer = SimulationImporter('simulations.db')

result = importer.import_from_csv(
    csv_path='data2.csv',
    simulation_name='Current Mirror W Sweep - Iref=100uA',
    circuit_name='Simple Current Mirror NMOS',
    description='Full parametric sweep of transistor widths',
    categories=['Current Mirror', 'NMOS', 'Parametric Sweep'],
    parameters={
        'Iref': {'value': 100e-6, 'unit': 'A'},
        'Vov': {'value': 0.2, 'unit': 'V'},
        'L': {'value': 540e-9, 'unit': 'm'}
    },
    vdd=1.8,
    vt=0.5,
    temperature=27
)

print(f"Imported {result['data_series_count']} data series")
print(f"Total data points: {result['data_points_count']}")
```

---

## Query Module

### `query/__init__.py`

**Exports:**
- `SimulationQuery` - Query interface for simulation data

---

### `class SimulationQuery`

Query and filter simulation data from the database.

#### `__init__(self)`

**Example:**
```python
from database import init_database
from query import SimulationQuery

init_database('simulations.db')
query = SimulationQuery()
```

---

#### `search_simulations(keyword: str) -> List[dict]`

Search for simulations by keyword in name, description, or categories.

**Parameters:**
- `keyword` (str): Search keyword

**Returns:**
```python
[
    {
        'simulation_id': int,
        'name': str,
        'circuit_name': str,
        'description': str,
        'categories': [str, ...],
        'created_at': str
    },
    ...
]
```

**Example:**
```python
results = query.search_simulations('current mirror')
for sim in results:
    print(f"{sim['name']} - {sim['circuit_name']}")
```

---

#### `filter_by_metric(metric_name, min_value=None, max_value=None, limit=None, simulation_id=None) -> List[dict]`

Filter data series by optimization metric values. **Returns sweep parameters!** ⭐

**Parameters:**
- `metric_name` (str): Metric to filter by (`'error_percentage'`, `'gain'`, `'bandwidth'`)
- `min_value` (float, optional): Minimum metric value
- `max_value` (float, optional): Maximum metric value
- `limit` (int, optional): Maximum number of results
- `simulation_id` (int, optional): Filter to specific simulation

**Returns:**
```python
[
    {
        'simulation_id': int,
        'simulation_name': str,
        'circuit_name': str,
        'metric_name': str,
        'metric_value': float,
        'metric_unit': str,
        'signal_path': str,
        'data_series_id': int,
        'sweep_parameters': {              # ⭐ NEW!
            'Nm_In_W': float,
            'Nm_Out_W': float
        }
    },
    ...
]
```

**Examples:**

**Find minimum error:**
```python
results = query.filter_by_metric('error_percentage', limit=1)
best = results[0]
print(f"Minimum error: {best['metric_value']:.2f}%")
print(f"Parameters: {best['sweep_parameters']}")
# Minimum error: 36.09%
# Parameters: {'Nm_In_W': 0.0001, 'Nm_Out_W': 2.282544e-05}
```

**Find configurations with error < 50%:**
```python
results = query.filter_by_metric('error_percentage', max_value=50.0)
print(f"Found {len(results)} good configurations")
```

**Find high gain configurations:**
```python
results = query.filter_by_metric('gain', min_value=0.9, max_value=1.1, limit=20)
for r in results:
    print(f"Gain: {r['metric_value']:.4f}, Params: {r['sweep_parameters']}")
```

---

#### `get_simulation_details(simulation_id: int) -> dict`

Get complete details for a simulation.

**Parameters:**
- `simulation_id` (int): Simulation ID

**Returns:**
```python
{
    'simulation_id': int,
    'name': str,
    'circuit_name': str,
    'description': str,
    'vdd': float,
    'vt': float,
    'temperature': float,
    'created_at': str,
    'categories': [str, ...],
    'parameters': {
        'param_name': {'value': float, 'unit': str}
    },
    'sweep_configuration': {
        'sweep_id': int,
        'parameters': [
            {
                'name': str,
                'start': float,
                'end': float,
                'points': int
            }
        ]
    },
    'data_series_count': int
}
```

**Example:**
```python
details = query.get_simulation_details(simulation_id=1)
print(f"Circuit: {details['circuit_name']}")
print(f"Categories: {', '.join(details['categories'])}")
print(f"Data series: {details['data_series_count']}")
print(f"Parameters: {details['parameters']}")
```

---

#### `get_data_series(data_series_id: int) -> dict`

Get all data points for a specific data series.

**Parameters:**
- `data_series_id` (int): Data series ID

**Returns:**
```python
{
    'data_series_id': int,
    'simulation_id': int,
    'signal_path': str,
    'sweep_parameters': {
        'param_name': float
    },
    'x_values': np.ndarray,    # NumPy array
    'y_values': np.ndarray,    # NumPy array
    'point_count': int
}
```

**Example:**
```python
data = query.get_data_series(data_series_id=2488)
print(f"Signal: {data['signal_path']}")
print(f"Parameters: {data['sweep_parameters']}")
print(f"Points: {data['point_count']}")

# Plot the data
import matplotlib.pyplot as plt
plt.plot(data['x_values'], data['y_values'])
plt.xlabel('Frequency (Hz)')
plt.ylabel('Current (A)')
plt.show()
```

---

#### `list_categories() -> List[dict]`

Get all categories with simulation counts.

**Returns:**
```python
[
    {
        'category_name': str,
        'simulation_count': int
    },
    ...
]
```

**Example:**
```python
categories = query.list_categories()
for cat in categories:
    print(f"{cat['category_name']}: {cat['simulation_count']} simulations")
```

---

#### `get_metric_statistics(metric_name: str, simulation_id: int = None) -> dict`

Get statistical summary of a metric.

**Parameters:**
- `metric_name` (str): Metric name (`'error_percentage'`, `'gain'`, `'bandwidth'`)
- `simulation_id` (int, optional): Filter to specific simulation

**Returns:**
```python
{
    'metric_name': str,
    'min': float,
    'max': float,
    'mean': float,
    'median': float,
    'std_dev': float,
    'count': int
}
```

**Example:**
```python
stats = query.get_metric_statistics('error_percentage', simulation_id=1)
print(f"Error range: {stats['min']:.2f}% to {stats['max']:.2f}%")
print(f"Mean: {stats['mean']:.2f}%, Median: {stats['median']:.2f}%")
print(f"Std Dev: {stats['std_dev']:.2f}%")
print(f"Total configurations: {stats['count']}")
```

---

## Chatbot Module

### `chatbot/__init__.py`

**Exports:**
- `CircuitChatbot` - OpenAI-powered chatbot interface

---

### `class CircuitChatbot`

Natural language interface for querying simulation data.

#### `__init__(self, api_key: str, db_path: str = 'simulations.db')`

**Parameters:**
- `api_key` (str): OpenAI API key
- `db_path` (str): Path to database file

**Example:**
```python
from chatbot import CircuitChatbot

chatbot = CircuitChatbot(api_key='sk-...', db_path='simulations.db')
```

---

#### `chat(message: str) -> str`

Send a message and get a response.

**Parameters:**
- `message` (str): User's question or request

**Returns:**
- Response string from ChatGPT

**Example:**
```python
response = chatbot.chat("What's the minimum error achieved?")
print(response)
# "The minimum error is 36.09%, achieved with Nm_In_W=100µm and Nm_Out_W=22.83µm."
```

---

#### `start_interactive_session()`

Start an interactive chat session in the terminal.

**Example:**
```python
chatbot.start_interactive_session()
# Starts interactive loop - type 'quit' to exit
```

---

### Available Chatbot Tools

The chatbot has access to 6 tools (automatically called based on user questions):

1. **`search_simulations`** - Find simulations by keyword
2. **`filter_by_metric`** - Filter by error, gain, bandwidth
3. **`get_simulation_details`** - Get full simulation info
4. **`get_data_series`** - Get raw X,Y data
5. **`list_categories`** - List all categories
6. **`get_metric_statistics`** - Get statistical summaries

**Example Questions:**

```
"Find simulations about current mirrors"
"Show me configurations with error less than 40%"
"What's the minimum error achieved?"
"Give me the sweep parameters for the best configuration"
"What categories do we have?"
"Get statistics for error_percentage"
"Show me the data for series ID 2488"
"List all simulations"
```

---

## CLI Module

### `cli.py`

Command-line interface for the system.

---

### `import` Command

Import a CSV file into the database.

**Usage:**
```bash
python3 cli.py import CSV_FILE [OPTIONS]
```

**Options:**
- `--name TEXT` - Simulation name (required)
- `--circuit TEXT` - Circuit name (required)
- `--description TEXT` - Description (required)
- `--categories TEXT...` - Category tags (multiple allowed)
- `--parameters TEXT...` - Parameters in format `name:value:unit`
- `--vdd FLOAT` - Supply voltage in volts (required)
- `--vt FLOAT` - Threshold voltage in volts (required)
- `--temperature FLOAT` - Temperature in Celsius (required)

**Example:**
```bash
python3 cli.py import data2.csv \
  --name "Current Mirror W Sweep - Iref=100uA" \
  --circuit "Simple Current Mirror NMOS" \
  --description "Full parametric sweep of transistor widths" \
  --categories "Current Mirror" "NMOS" "Parametric Sweep" \
  --parameters Iref:100e-6:A Vov:0.2:V L:540e-9:m \
  --vdd 1.8 \
  --vt 0.5 \
  --temperature 27
```

---

### `chat` Command

Start an interactive chatbot session.

**Usage:**
```bash
python3 cli.py chat
```

**Example:**
```bash
$ python3 cli.py chat
Starting Circuit Simulation Chatbot...
Type 'quit' to exit.

You: What's the minimum error?
Bot: The minimum error is 36.09%, achieved with Nm_In_W=100µm and Nm_Out_W=22.83µm.

You: Show me all configurations with error < 50%
Bot: Found 20 configurations with error less than 50%. Here are the top 10:
     1. 36.09% (Nm_In_W=100µm, Nm_Out_W=22.83µm)
     2. 36.51% (Nm_In_W=88.42µm, Nm_Out_W=20.18µm)
     ...

You: quit
Goodbye!
```

---

## Utility Scripts

### `check_status.py`

Check database status and statistics.

**Usage:**
```bash
python3 check_status.py
```

**Output:**
```
=== Database Status ===
Database: simulations.db

Simulations: 1
Data Series: 2500
Data Points: 1621100
Categories: 3
Metrics: 2500

=== Recent Simulations ===
1. Current Mirror W Sweep - Iref=100uA
   Circuit: Simple Current Mirror NMOS
   Created: 2025-10-21 18:15:23
   Data Series: 2500
```

---

### `import_efficient.py`

Batch importer for large CSV files (50MB+).

**Usage:**
1. Edit the file to set parameters
2. Run: `python3 import_efficient.py`

**Features:**
- Processes 10 series per batch
- Progress tracking
- Memory efficient
- Automatic metric calculation

**Example Output:**
```
Starting efficient import...
File: data2.csv

Processing batch 1/2500 (Series 1-10)...
✓ Batch 1/2500 completed

Processing batch 2/2500 (Series 11-20)...
✓ Batch 2/2500 completed

...

Import completed successfully!
Total data series: 2500
Total data points: 1621100
```

---

### `test_sweep_params.py`

Test sweep parameter queries.

**Usage:**
```bash
python3 test_sweep_params.py
```

**Output:**
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

## Quick Reference

### Common Tasks

**Initialize database:**
```python
from database import init_database
init_database('simulations.db')
```

**Import CSV:**
```bash
python3 cli.py import file.csv --name "..." --circuit "..." --description "..." \
  --categories "..." --parameters "..." --vdd 1.8 --vt 0.5 --temperature 27
```

**Find minimum error:**
```python
from query import SimulationQuery
query = SimulationQuery()
results = query.filter_by_metric('error_percentage', limit=1)
print(results[0]['sweep_parameters'])
```

**Start chatbot:**
```bash
python3 cli.py chat
```

**Check status:**
```bash
python3 check_status.py
```

---

## Error Handling

All functions include proper error handling:

```python
try:
    results = query.filter_by_metric('error_percentage', limit=10)
except Exception as e:
    print(f"Error: {e}")
```

Common exceptions:
- `FileNotFoundError` - CSV file not found
- `ValueError` - Invalid parameter format
- `SQLAlchemyError` - Database operation failed
- `KeyError` - Missing required field

---

## Best Practices

1. **Always initialize database first:**
   ```python
   init_database('simulations.db')
   ```

2. **Use context managers for sessions:**
   ```python
   with get_session() as session:
       # Your queries here
   ```

3. **Batch large imports:**
   - Use `import_efficient.py` for files > 50MB

4. **Include sweep parameters in queries:**
   - Use updated `filter_by_metric()` that returns `sweep_parameters`

5. **Check errors:**
   - Always wrap database operations in try/except

6. **Close chatbot properly:**
   - Type 'quit' to exit interactive session

---

## Performance Notes

- **Database size:** ~200MB for 2,500 series with 653 points each
- **Import speed:** ~100 series/minute for batch import
- **Query speed:** < 1 second for most queries
- **Chatbot latency:** 2-5 seconds per response (OpenAI API call)

---

## Version History

- **v1.0** - Initial release with 9-table database
- **v1.1** - Added batch importer for large files
- **v1.2** - Added sweep parameter returns in queries ⭐
- **v1.3** - Enhanced documentation and API reference

---

For more information, see:
- `documentation/PROJECT_COMPLETE_SUMMARY.md` - Full project overview
- `documentation/DATABASE_SCHEMA.md` - Database structure
- `documentation/USAGE_GUIDE.md` - Usage examples
- `documentation/API_SWEEP_PARAMETERS.md` - Sweep parameter feature

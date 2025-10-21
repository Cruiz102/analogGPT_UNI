# Quick Start Guide

## Installation & Setup

### 1. Activate Virtual Environment
```bash
cd /home/cesar/Projects/ciic_circuits_research
source .venv/bin/activate
```

### 2. Install Dependencies (if not already installed)
```bash
pip install -r requirements.txt
```

### 3. Set OpenAI API Key (for chatbot)
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage Examples

### Example 1: Import Simulation Data

Import one of your CSV files:

```bash
python cli.py import data.csv \
  --name "Current Mirror W Sweep - Full Analysis" \
  --circuit "Simple Current Mirror NMOS" \
  --description "Complete parametric sweep of input and output widths" \
  --categories "Current Mirror" "NMOS" "Parametric Sweep" \
  --parameters Iref:100e-6:A Vov:0.2:V L:540e-9:m \
  --vdd 1.8 \
  --vt 0.5 \
  --temperature 27
```

**Note**: The CSV files in this workspace are very large (>50MB). The import may take several minutes.

### Example 2: Run Test with Sample Data

Test the system with a small generated dataset:

```bash
python test_system.py
```

This creates a small test CSV, imports it, and runs all query functions.

### Example 3: Start the Chatbot

```bash
python cli.py chat
```

Then ask questions like:
- "Show me all current mirror simulations"
- "Find simulations with error percentage less than 5%"
- "What are the parameters for simulation ID 1?"
- "Get statistics for the gain metric"
- "Show me data series where Nm_In_W is 2.4e-07"

### Example 4: Programmatic Usage

```python
from database import init_database
from ingestion import SimulationImporter
from query import SimulationQuery

# Initialize
init_database('my_simulations.db')

# Import
importer = SimulationImporter()
sim = importer.import_from_csv(
    csv_path='data.csv',
    simulation_name='My Simulation',
    circuit_name='Current Mirror',
    categories=['Test'],
    fixed_parameters={'Iref': (100e-6, 'A')},
    assumptions={'vdd': 1.8, 'vt': 0.5}
)

# Query
query = SimulationQuery()
results = query.filter_by_metric('error_percentage', max_value=5.0)
print(f"Found {len(results)} simulations with low error")
```

## Command Reference

### Import Command

```bash
python cli.py import <csv_file> [options]
```

**Required:**
- `--name`: Simulation name
- `--circuit`: Circuit name

**Optional:**
- `--description`: Description
- `--categories`: Space-separated categories
- `--parameters`: Fixed parameters (format: name:value:unit)
- `--vdd`: Supply voltage
- `--vt`: Threshold voltage
- `--temperature`: Temperature in Celsius
- `--no-metrics`: Skip automatic metric calculation
- `--database`: Database file path (default: simulations.db)

### Chat Command

```bash
python cli.py chat [options]
```

**Optional:**
- `--api-key`: OpenAI API key (or set OPENAI_API_KEY env var)
- `--model`: Model name (default: gpt-4-turbo-preview)
- `--database`: Database file path (default: simulations.db)

## Query Examples (Python)

### Search Simulations
```python
query = SimulationQuery()

# All simulations
all_sims = query.search_simulations()

# By circuit name
mirrors = query.search_simulations(circuit_name='Current Mirror')

# By category
test_sims = query.search_simulations(categories=['Test'])
```

### Filter by Metrics
```python
# Low error percentage
low_error = query.filter_by_metric(
    metric_name='error_percentage',
    max_value=5.0
)

# High gain
high_gain = query.filter_by_metric(
    metric_name='gain',
    min_value=1.2
)
```

### Get Details
```python
# Simulation details
details = query.get_simulation_details(1)
print(details['name'])
print(details['parameters'])
print(details['metrics'])

# Data series
series = query.get_data_series(
    simulation_id=1,
    signal_path='/I4/Out',
    sweep_filters={'Nm_In_W': 2.4e-07}
)

for s in series:
    print(f"Signal: {s['signal_path']}")
    for point in s['data_points']:
        print(f"  X={point['x']}, Y={point['y']}")
```

### Statistics
```python
# Metric statistics
stats = query.get_metric_statistics('error_percentage')
print(f"Min: {stats['min']}, Max: {stats['max']}, Avg: {stats['avg']}")

# Categories
categories = query.list_categories()
for cat in categories:
    print(f"{cat['name']}: {cat['simulation_count']} simulations")
```

## Troubleshooting

### Large CSV Files
If importing large CSV files (>50MB), be patient. The import may take several minutes as it:
1. Parses all column headers
2. Extracts sweep parameters
3. Imports all data points
4. Calculates metrics

### Memory Issues
For very large CSV files, consider:
1. Splitting the CSV into smaller files
2. Importing one series at a time
3. Increasing available memory

### OpenAI API Errors
- Ensure API key is set correctly
- Check API quota and billing
- Verify network connectivity

## Next Steps

1. **Import Your Data**: Use `python cli.py import` to load your simulation data
2. **Explore with Chatbot**: Use `python cli.py chat` for natural language queries
3. **Build Custom Tools**: Extend the chatbot with Virtuoso integration for running simulations
4. **Add Visualizations**: Create plotting functions for data series
5. **Export Results**: Add export functionality for filtered results

## Project Structure

```
ciic_circuits_research/
├── database/           # Database models and connection
├── parsers/            # CSV parsers
├── ingestion/          # Data import
├── query/              # Query interface
├── chatbot/            # OpenAI integration
├── cli.py              # Command-line interface
├── test_system.py      # Test script
├── example_usage.py    # Example demonstrations
└── requirements.txt    # Dependencies
```

## Support

For issues or questions:
1. Check the README_NEW.md for detailed information
2. Review the example_usage.py for code examples
3. Run test_system.py to verify installation

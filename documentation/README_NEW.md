# Circuit Simulation Database and Chatbot

A comprehensive application for managing and querying Cadence circuit simulation data using a chatbot interface powered by OpenAI.

## Features

- **SQLite Database**: Store circuit simulation data with support for:
  - Multiple sweep parameters
  - Time-series or parametric data
  - Optimization metrics (error percentage, gain, etc.)
  - Categories and tags
  - Fixed simulation parameters

- **CSV Parser**: Import Cadence simulation CSV files with complex formats
  - Handles repeating X,Y column pairs
  - Extracts sweep parameters from headers
  - Calculates optimization metrics automatically

- **Query Interface**: Powerful search and filtering capabilities
  - Search by name, circuit, or category
  - Filter by metric values (e.g., error percentage < 5%)
  - Retrieve detailed simulation data
  - Get statistics across simulations

- **Chatbot Interface**: Natural language queries using OpenAI
  - Ask questions about simulations in plain English
  - Automatic function calling to query database
  - Context-aware conversations
  - Future: Integration with Virtuoso CLI for running simulations

## Installation

1. Clone the repository:
```bash
cd /home/cesar/Projects/ciic_circuits_research
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Project Structure

```
ciic_circuits_research/
├── database/           # Database models and connection
│   ├── __init__.py
│   ├── models.py       # SQLAlchemy models
│   └── connection.py   # Database connection manager
├── parsers/            # CSV parsers
│   ├── __init__.py
│   └── csv_parser.py   # Cadence CSV parser
├── ingestion/          # Data import modules
│   ├── __init__.py
│   └── importer.py     # Simulation importer
├── query/              # Query interface
│   ├── __init__.py
│   └── interface.py    # Query functions
├── chatbot/            # OpenAI chatbot
│   ├── __init__.py
│   └── openai_interface.py  # Chatbot implementation
├── cli.py              # Command-line interface
├── example_usage.py    # Example usage script
└── requirements.txt    # Python dependencies
```

## Usage

### Importing Simulations

Import a simulation from a CSV file:

```bash
python cli.py import data.csv \
  --name "Current Mirror W Sweep" \
  --circuit "Simple Current Mirror NMOS" \
  --description "Sweep of input and output widths with RL and CL" \
  --categories "Current Mirror" "NMOS" "Parametric Sweep" \
  --parameters Iref:100e-6:A Vov:0.2:V L:540e-9:m \
  --vdd 1.8 \
  --vt 0.5
```

### Running the Chatbot

Start an interactive chatbot session:

```bash
python cli.py chat
```

Example queries:
- "Show me all current mirror simulations"
- "Find simulations with error percentage less than 5%"
- "What are the parameters for simulation ID 1?"
- "Get the gain statistics for current mirrors"
- "Show me data series for simulation 1 where Nm_In_W is 2.4e-07"

### Programmatic Usage

```python
from database import init_database
from ingestion import SimulationImporter
from query import SimulationQuery

# Initialize database
init_database('simulations.db')

# Import a simulation
importer = SimulationImporter()
simulation = importer.import_from_csv(
    csv_path='data.csv',
    simulation_name='Current Mirror Test',
    circuit_name='Current Mirror',
    description='Test simulation',
    categories=['Current Mirror', 'Test'],
    fixed_parameters={
        'Iref': (100e-6, 'A'),
        'Vov': (0.2, 'V'),
        'L': (540e-9, 'm')
    },
    assumptions={
        'vdd': 1.8,
        'vt': 0.5
    }
)

# Query simulations
query = SimulationQuery()

# Search by name
results = query.search_simulations(circuit_name='Current Mirror')

# Filter by metric
low_error = query.filter_by_metric(
    metric_name='error_percentage',
    max_value=5.0
)

# Get simulation details
details = query.get_simulation_details(simulation.id)
```

## Database Schema

### Main Tables

- **simulations**: Simulation metadata (name, circuit, description, assumptions)
- **categories**: Categories for organizing simulations
- **simulation_parameters**: Fixed parameters (Iref, Vov, L, etc.)
- **sweep_configurations**: Swept parameter definitions
- **sweep_values**: Individual values for swept parameters
- **data_series**: Data series with specific sweep parameter values
- **data_series_sweep_params**: Links data series to sweep parameter values
- **data_points**: Individual X,Y data points
- **optimization_metrics**: Calculated metrics (error percentage, gain, etc.)

## CSV Format

The parser supports Cadence CSV files with the following format:

```
"/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) X","/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) Y", ...
1e-09,1e-09, ...
1.1e-09,1.05e-09, ...
...
```

- Headers contain signal path and sweep parameters
- Columns come in X,Y pairs
- Each pair represents a different sweep configuration

## Optimization Metrics

The system automatically calculates:

- **error_percentage**: Average percentage error between output and expected value
- **gain**: Average gain (Y/X ratio)

Custom metrics can be added by extending the parser.

## Future Enhancements

- **Virtuoso Integration**: Tools for running simulations via Virtuoso CLI
- **Advanced Metrics**: Bandwidth, phase margin, settling time, etc.
- **Visualization**: Plot data series and metrics
- **Comparison**: Compare multiple simulations side-by-side
- **Export**: Export filtered results to CSV or reports

## Example: Current Mirror

For a current mirror circuit with:
- Input: Iref = 100 µA
- Vov = 0.2 V
- L = 540 nm
- Vdd = 1.8 V
- Vt = 0.5 V

The system stores:
1. Fixed parameters (Iref, Vov, L)
2. Sweep parameters (Nm_In_W, Nm_Out_W)
3. Data points (input current vs. output current)
4. Calculated metrics (error percentage, gain)

You can then query:
- "Find current mirrors with error < 5%"
- "Show simulations where Nm_In_W = 2.4e-07"
- "What's the average gain for current mirrors?"

## License

MIT License

## Author

CIIC Circuits Research Team

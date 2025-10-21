# Database Schema Documentation

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SIMULATIONS (Core)                              │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ name                    - Simulation name                               │
│ circuit_name            - Circuit being simulated                       │
│ description             - Detailed description                          │
│ created_at              - Timestamp                                     │
│ vdd, vt, temperature    - Assumptions                                   │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ├─── (1:N) ───┐
            │             │
            │             ▼
            │     ┌─────────────────────────────────┐
            │     │   SIMULATION_PARAMETERS         │
            │     ├─────────────────────────────────┤
            │     │ id (PK)                         │
            │     │ simulation_id (FK)              │
            │     │ parameter_name  - e.g., "Iref"  │
            │     │ parameter_value - e.g., 100e-6  │
            │     │ unit            - e.g., "A"     │
            │     └─────────────────────────────────┘
            │
            ├─── (1:N) ───┐
            │             │
            │             ▼
            │     ┌─────────────────────────────────┐
            │     │   SWEEP_CONFIGURATIONS          │
            │     ├─────────────────────────────────┤
            │     │ id (PK)                         │
            │     │ simulation_id (FK)              │
            │     │ parameter_name - e.g., "Nm_In_W"│
            │     └─────────────────────────────────┘
            │              │
            │              │ (1:N)
            │              ▼
            │     ┌─────────────────────────────────┐
            │     │   SWEEP_VALUES                  │
            │     ├─────────────────────────────────┤
            │     │ id (PK)                         │
            │     │ sweep_config_id (FK)            │
            │     │ value       - e.g., 2.4e-07     │
            │     └─────────────────────────────────┘
            │
            ├─── (1:N) ───┐
            │             │
            │             ▼
            │     ┌─────────────────────────────────┐
            │     │   DATA_SERIES                   │
            │     ├─────────────────────────────────┤
            │     │ id (PK)                         │
            │     │ simulation_id (FK)              │
            │     │ signal_path  - e.g., "/I4/Out"  │
            │     └─────────────────────────────────┘
            │              │
            │              ├── (1:N) ──┐
            │              │            │
            │              │            ▼
            │              │   ┌──────────────────────────────────┐
            │              │   │ DATA_SERIES_SWEEP_PARAMS         │
            │              │   ├──────────────────────────────────┤
            │              │   │ id (PK)                          │
            │              │   │ data_series_id (FK)              │
            │              │   │ parameter_name - e.g., "Nm_In_W" │
            │              │   │ parameter_value - e.g., 2.4e-07  │
            │              │   └──────────────────────────────────┘
            │              │
            │              └── (1:N) ──┐
            │                           │
            │                           ▼
            │                  ┌─────────────────────────────┐
            │                  │   DATA_POINTS               │
            │                  ├─────────────────────────────┤
            │                  │ id (PK)                     │
            │                  │ data_series_id (FK)         │
            │                  │ x_value  - Input value      │
            │                  │ y_value  - Output value     │
            │                  │ sequence - Order            │
            │                  └─────────────────────────────┘
            │
            ├─── (1:N) ───┐
            │             │
            │             ▼
            │     ┌─────────────────────────────────────────┐
            │     │   OPTIMIZATION_METRICS                  │
            │     ├─────────────────────────────────────────┤
            │     │ id (PK)                                 │
            │     │ simulation_id (FK)                      │
            │     │ data_series_id (FK, optional)           │
            │     │ metric_name  - e.g., "error_percentage" │
            │     │ metric_value - e.g., 5.2                │
            │     │ unit         - e.g., "%"                │
            │     └─────────────────────────────────────────┘
            │
            └─── (M:N) ───┐
                          │
                          ▼
                 ┌──────────────────────────┐
                 │   CATEGORIES             │
                 ├──────────────────────────┤
                 │ id (PK)                  │
                 │ name - e.g., "Current    │
                 │        Mirror"           │
                 │ description              │
                 └──────────────────────────┘
                          ▲
                          │
                 ┌────────┴────────┐
                 │ SIMULATION_     │
                 │ CATEGORIES      │
                 │ (join table)    │
                 └─────────────────┘
```

## Table Descriptions

### Core Tables

#### SIMULATIONS
The main table storing simulation metadata. Each record represents a complete simulation run.

**Key Fields:**
- `name`: Descriptive name (e.g., "Current Mirror W Sweep - Bode Analysis")
- `circuit_name`: Type of circuit (e.g., "Simple Current Mirror NMOS")
- `description`: Detailed explanation of the simulation
- `vdd`, `vt`, `temperature`: Environmental assumptions

#### SIMULATION_PARAMETERS
Fixed parameters for a simulation (not swept).

**Example:**
- Iref = 100 µA
- Vov = 0.2 V
- L = 540 nm

#### SWEEP_CONFIGURATIONS
Defines which parameters are swept in the simulation.

**Example:**
- Nm_In_W (input width)
- Nm_Out_W (output width)

#### SWEEP_VALUES
Individual values for each swept parameter.

**Example for Nm_In_W:**
- 2.4e-07
- 2.714415e-07
- 3.070021e-07
- ...

### Data Tables

#### DATA_SERIES
Each series represents one combination of sweep parameter values.

**Example:**
- Signal: /I4/Out
- Nm_In_W = 2.4e-07
- Nm_Out_W = 2.4e-07

#### DATA_SERIES_SWEEP_PARAMS
Links a data series to its specific sweep parameter values.

#### DATA_POINTS
Individual measurements (X,Y pairs).

**Example for Current Mirror:**
- X: Input current
- Y: Output current

### Analysis Tables

#### OPTIMIZATION_METRICS
Calculated metrics for evaluation.

**Common Metrics:**
- `error_percentage`: % difference from ideal
- `gain`: Y/X ratio
- `bandwidth`: Frequency response (future)
- `phase_margin`: Stability metric (future)

#### CATEGORIES
Organize simulations into groups.

**Examples:**
- Current Mirror
- NMOS
- PMOS
- Bode Plot
- Transient Analysis
- Parametric Sweep

## Data Flow

```
CSV File
   │
   ▼
Parser (parsers/csv_parser.py)
   │
   ├─ Extract headers
   ├─ Parse sweep parameters
   └─ Read data points
   │
   ▼
Importer (ingestion/importer.py)
   │
   ├─ Create simulation record
   ├─ Add parameters & assumptions
   ├─ Add sweep configurations
   ├─ Add data series & points
   └─ Calculate metrics
   │
   ▼
Database (SQLite)
   │
   ▼
Query Interface (query/interface.py)
   │
   ├─ Search simulations
   ├─ Filter by metrics
   ├─ Get data series
   └─ Calculate statistics
   │
   ▼
Chatbot (chatbot/openai_interface.py)
   │
   └─ Natural language queries
```

## Example Data

### Simulation
```
ID: 1
Name: "Current Mirror W Sweep"
Circuit: "Simple Current Mirror NMOS"
Vdd: 1.8V, Vt: 0.5V
```

### Parameters
```
Iref: 100e-6 A
Vov: 0.2 V
L: 540e-9 m
```

### Sweep Configuration
```
Nm_In_W: [2.4e-07, 2.714e-07, 3.07e-07, ...]
Nm_Out_W: [2.4e-07, 2.714e-07, 3.07e-07, ...]
```

### Data Series (one of many)
```
Signal: /I4/Out
Nm_In_W: 2.4e-07
Nm_Out_W: 3.0e-07
Points: [(1e-9, 1.25e-9), (2e-9, 2.5e-9), ...]
```

### Metrics
```
error_percentage: 25.0%
gain: 1.25
```

## Query Examples

### Find Low Error Simulations
```sql
SELECT s.name, om.metric_value
FROM simulations s
JOIN optimization_metrics om ON s.id = om.simulation_id
WHERE om.metric_name = 'error_percentage'
  AND om.metric_value < 5.0
ORDER BY om.metric_value;
```

### Get Data for Specific Sweep
```sql
SELECT dp.x_value, dp.y_value
FROM data_points dp
JOIN data_series ds ON dp.data_series_id = ds.id
JOIN data_series_sweep_params dssp ON ds.id = dssp.data_series_id
WHERE ds.simulation_id = 1
  AND dssp.parameter_name = 'Nm_In_W'
  AND dssp.parameter_value = 2.4e-07;
```

## Indexing Strategy

Indexes are created on:
- `simulations.name`
- `simulations.circuit_name`
- `optimization_metrics.metric_name`
- `optimization_metrics.metric_value`
- `data_points.data_series_id`

This ensures fast queries for common operations.

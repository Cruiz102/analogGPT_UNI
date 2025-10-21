# Query API Reference - Getting Sweep Parameters

## ✅ Updated API: Now Returns Sweep Parameters!

The `filter_by_metric()` function now returns **sweep parameter values** for each configuration, making it easy to identify the exact transistor dimensions that achieve optimal performance.

---

## 📊 Query Examples

### 1. Find Best Configurations (Lowest Error)

```python
from database import init_database
from query import SimulationQuery

init_database('simulations.db')
query = SimulationQuery()

# Get top 10 configurations with lowest error
results = query.filter_by_metric(
    metric_name='error_percentage',
    limit=10
)

for result in results:
    print(f"Error: {result['metric_value']:.2f}%")
    print(f"Sweep Parameters: {result['sweep_parameters']}")
```

**Output:**
```
Error: 36.09%
Sweep Parameters: {'Nm_In_W': 0.0001, 'Nm_Out_W': 2.282544e-05}
```

---

### 2. Find Configurations with Error < 50%

```python
# Get all configurations with acceptable error
good_configs = query.filter_by_metric(
    metric_name='error_percentage',
    max_value=50.0
)

print(f"Found {len(good_configs)} good configurations")
```

---

### 3. Find High Gain Configurations

```python
# Get configurations with gain close to desired ratio
high_gain = query.filter_by_metric(
    metric_name='gain',
    min_value=0.9,
    max_value=1.1,
    limit=20
)

for result in high_gain:
    print(f"Gain: {result['metric_value']:.4f}")
    params = result['sweep_parameters']
    print(f"  Nm_In_W: {params['Nm_In_W']:.6e}")
    print(f"  Nm_Out_W: {params['Nm_Out_W']:.6e}")
```

---

## 🤖 Chatbot Queries

The chatbot now has access to sweep parameters! You can ask:

### Find Minimum Error Configuration
```
You: "Give me the sweep parameter values for the configuration with minimum error"
```

**Response:**
```
The minimum error of 36.09% is achieved with:
- Nm_In_W (Input Width): 1.000000e-04 (100 µm)
- Nm_Out_W (Output Width): 2.282544e-05 (22.83 µm)
- Signal Path: /I4/Out
```

### Find Configurations by Error Range
```
You: "Show me all configurations with error between 36% and 40%"
```

### Find Optimal Width Ratios
```
You: "What's the ratio of Nm_Out_W to Nm_In_W for the best configurations?"
```

---

## 📈 Results from Your Current Mirror Simulation

### Top 10 Best Configurations

| Rank | Error (%) | Nm_In_W (µm) | Nm_Out_W (µm) | Ratio (Out/In) |
|------|-----------|--------------|---------------|----------------|
| 1    | 36.09     | 100.0        | 22.83         | 0.228          |
| 2    | 36.51     | 88.42        | 20.18         | 0.228          |
| 3    | 36.96     | 78.18        | 17.84         | 0.228          |
| 4    | 37.42     | 69.12        | 15.78         | 0.228          |
| 5    | 37.49     | 100.0        | 25.82         | 0.258          |
| 6    | 37.77     | 88.42        | 22.83         | 0.258          |
| 7    | 37.90     | 61.11        | 13.95         | 0.228          |
| 8    | 38.08     | 78.18        | 20.18         | 0.258          |
| 9    | 38.40     | 54.03        | 12.33         | 0.228          |
| 10   | 38.41     | 69.12        | 17.84         | 0.258          |

### Key Insights

1. **Optimal Ratio**: The best configurations have W_out/W_in ≈ 0.228 (roughly 1:4.4)
2. **Larger Input Width**: Maximum input width (100 µm) gives best results
3. **Consistent Pattern**: The optimal ratio is consistent across different absolute widths
4. **Minimum Error**: Even the best configuration has 36% error, suggesting:
   - Non-ideal current source
   - Channel length modulation effects
   - Mismatch considerations

---

## 🔧 Direct Python Usage

### Get Minimum Error with Parameters

```python
from database import init_database
from query import SimulationQuery

init_database('simulations.db')
query = SimulationQuery()

# Get configuration with minimum error
min_error = query.filter_by_metric('error_percentage', limit=1)[0]

print(f"Minimum Error: {min_error['metric_value']:.2f}%")
print(f"\nOptimal Parameters:")
for param, value in min_error['sweep_parameters'].items():
    print(f"  {param}: {value:.6e} ({value*1e6:.2f} µm)")
```

---

## 💾 Complete Result Structure

Each result from `filter_by_metric()` now contains:

```python
{
    'simulation_id': 1,
    'simulation_name': 'Current Mirror W Sweep - Iref=100uA',
    'circuit_name': 'Simple Current Mirror NMOS',
    'metric_name': 'error_percentage',
    'metric_value': 36.09,
    'metric_unit': '%',
    'signal_path': '/I4/Out',
    'data_series_id': 2488,
    'sweep_parameters': {
        'Nm_In_W': 1.0e-04,    # 100 µm
        'Nm_Out_W': 2.28e-05   # 22.83 µm
    }
}
```

---

## 🎯 Next Steps

1. **Analyze the optimal ratio** (0.228) - why does this give minimum error?
2. **Check gain** for these configurations
3. **Verify** with hand calculations using square-law MOSFET equations
4. **Consider** channel-length modulation (λ) effects
5. **Explore** other metrics like output resistance, bandwidth

---

## 📞 Usage in Chatbot

The chatbot automatically uses this updated API, so it will now return sweep parameters when you ask:

- "What parameters give minimum error?"
- "Show me the best configurations"
- "Find configurations with error less than 40%"

The chatbot will now include **Nm_In_W** and **Nm_Out_W** values in its responses!

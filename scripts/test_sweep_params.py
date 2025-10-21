#!/usr/bin/env python3
"""
Test the updated filter_by_metric to show sweep parameters.
"""
from database import init_database
from query import SimulationQuery

init_database('simulations.db')
query = SimulationQuery()

print("\n" + "="*70)
print("FINDING BEST CURRENT MIRROR CONFIGURATIONS (Lowest Error)")
print("="*70 + "\n")

# Get configurations with lowest error (top 10)
results = query.filter_by_metric(
    metric_name='error_percentage',
    limit=10
)

if results:
    print(f"Found {len(results)} configurations with lowest error:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Error: {result['metric_value']:.2f}%")
        print(f"   Signal: {result['signal_path']}")
        
        if 'sweep_parameters' in result:
            print(f"   Sweep Parameters:")
            for param_name, param_value in result['sweep_parameters'].items():
                print(f"      - {param_name}: {param_value:.6e}")
        print()
else:
    print("No results found.")

print("\n" + "="*70)
print("FINDING CONFIGURATIONS WITH ERROR < 50%")
print("="*70 + "\n")

# Get configurations with error < 50%
good_results = query.filter_by_metric(
    metric_name='error_percentage',
    max_value=50.0,
    limit=20
)

print(f"Found {len(good_results)} configurations with error < 50%\n")

if good_results:
    print("Top 5 configurations:")
    for i, result in enumerate(good_results[:5], 1):
        print(f"\n{i}. Error: {result['metric_value']:.2f}%")
        if 'sweep_parameters' in result:
            for param_name, param_value in result['sweep_parameters'].items():
                print(f"   {param_name}: {param_value:.6e}")

print("\n" + "="*70 + "\n")

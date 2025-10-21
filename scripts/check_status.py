#!/usr/bin/env python3
"""
Quick check of database import status.
"""
from database import init_database
from query import SimulationQuery

def check_status():
    init_database('simulations.db')
    query = SimulationQuery()
    
    print("\n" + "="*60)
    print("DATABASE STATUS CHECK")
    print("="*60)
    
    # Check simulations
    sims = query.search_simulations()
    print(f"\n📊 Simulations: {len(sims)}")
    
    if sims:
        for sim in sims:
            print(f"\n  ✓ Simulation ID {sim['id']}: {sim['name']}")
            print(f"    Circuit: {sim['circuit_name']}")
            print(f"    Categories: {', '.join(sim['categories'])}")
            
            # Get details
            details = query.get_simulation_details(sim['id'])
            if details:
                print(f"\n    Parameters:")
                for param in details['parameters']:
                    print(f"      - {param['name']}: {param['value']} {param['unit']}")
                
                print(f"\n    Sweep Parameters:")
                for sp in details['sweep_parameters']:
                    print(f"      - {sp}")
                
                print(f"\n    Optimization Metrics:")
                error_metrics = [m for m in details['metrics'] if m['name'] == 'error_percentage']
                if error_metrics:
                    errors = [m['value'] for m in error_metrics]
                    print(f"      - Error %: min={min(errors):.2f}%, max={max(errors):.2f}%, avg={sum(errors)/len(errors):.2f}%")
                
                gain_metrics = [m for m in details['metrics'] if m['name'] == 'gain']
                if gain_metrics:
                    gains = [m['value'] for m in gain_metrics]
                    print(f"      - Gain: min={min(gains):.4f}, max={max(gains):.4f}, avg={sum(gains)/len(gains):.4f}")
                
                # Count data series
                data_series = query.get_data_series(sim['id'])
                print(f"\n    Data Series: {len(data_series)}")
                if data_series:
                    total_points = sum(len(ds['data_points']) for ds in data_series)
                    print(f"    Total Data Points: {total_points:,}")
    else:
        print("\n  ⚠️  No simulations found in database yet.")
        print("     The import may still be running...")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    check_status()

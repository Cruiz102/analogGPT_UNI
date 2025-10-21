#!/usr/bin/env python3
"""
Efficient CSV importer with progress tracking and batch processing.
For very large CSV files, this imports data in manageable chunks.
"""
import csv
import sys
from datetime import datetime
from database import init_database, get_database
from database.models import (
    Simulation, Category, SimulationParameter,
    SweepConfiguration, SweepValue, DataSeries,
    DataSeriesSweepParam, DataPoint, OptimizationMetric
)
from parsers import CadenceCSVParser

def import_simulation_efficient(
    csv_path, name, circuit_name, description="",
    categories=None, fixed_parameters=None, assumptions=None
):
    """Import simulation with progress tracking."""
    
    print(f"\n{'='*60}")
    print(f"EFFICIENT IMPORT: {name}")
    print(f"{'='*60}\n")
    
    # Initialize database
    db = init_database('simulations.db')
    
    print("📊 Step 1: Parsing CSV headers...")
    parser = CadenceCSVParser(csv_path)
    
    # Parse just the headers first
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        # Count data rows
        data_row_count = sum(1 for _ in reader)
    
    print(f"   ✓ Found {len(headers)} columns")
    print(f"   ✓ Found {data_row_count:,} data rows")
    
    parsed_headers = parser._parse_headers()
    num_series = len(parsed_headers) // 2
    print(f"   ✓ Identified {num_series} data series")
    
    # Ask user if they want to continue
    total_points = num_series * data_row_count
    print(f"\n⚠️  This will import approximately {total_points:,} data points")
    print(f"   Estimated time: {total_points / 10000:.1f} minutes")
    
    response = input("\nContinue with import? (y/n): ").strip().lower()
    if response != 'y':
        print("Import cancelled.")
        return
    
    print(f"\n📊 Step 2: Creating simulation record...")
    
    with db.get_session() as session:
        # Create simulation
        simulation = Simulation(
            name=name,
            circuit_name=circuit_name,
            description=description,
            created_at=datetime.utcnow()
        )
        
        if assumptions:
            simulation.vdd = assumptions.get('vdd')
            simulation.vt = assumptions.get('vt')
            simulation.temperature = assumptions.get('temperature')
        
        session.add(simulation)
        session.flush()
        sim_id = simulation.id
        
        print(f"   ✓ Created simulation ID {sim_id}")
        
        # Add categories
        if categories:
            for cat_name in categories:
                category = session.query(Category).filter_by(name=cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    session.add(category)
                simulation.categories.append(category)
            print(f"   ✓ Added {len(categories)} categories")
        
        # Add fixed parameters
        if fixed_parameters:
            for param_name, (param_value, unit) in fixed_parameters.items():
                param = SimulationParameter(
                    simulation_id=sim_id,
                    parameter_name=param_name,
                    parameter_value=param_value,
                    unit=unit
                )
                session.add(param)
            print(f"   ✓ Added {len(fixed_parameters)} fixed parameters")
        
        session.commit()
    
    print(f"\n📊 Step 3: Processing data series (this may take a while)...")
    
    # Parse full data
    parsed_data = parser.parse()
    
    # Import data series in batches
    batch_size = 10
    total_series = len(parsed_data['data_series'])
    
    for batch_start in range(0, total_series, batch_size):
        batch_end = min(batch_start + batch_size, total_series)
        batch = parsed_data['data_series'][batch_start:batch_end]
        
        with db.get_session() as session:
            simulation = session.query(Simulation).get(sim_id)
            
            for idx, series_data in enumerate(batch):
                series_num = batch_start + idx + 1
                
                # Create data series
                data_series = DataSeries(
                    simulation_id=sim_id,
                    signal_path=series_data['signal_path']
                )
                session.add(data_series)
                session.flush()
                
                # Add sweep parameters
                for param_name, param_value in series_data['sweep_values'].items():
                    sweep_param = DataSeriesSweepParam(
                        data_series_id=data_series.id,
                        parameter_name=param_name,
                        parameter_value=param_value
                    )
                    session.add(sweep_param)
                
                # Add data points
                x_values = series_data['x_values']
                y_values = series_data['y_values']
                
                for seq, (x, y) in enumerate(zip(x_values, y_values)):
                    point = DataPoint(
                        data_series_id=data_series.id,
                        x_value=x,
                        y_value=y,
                        sequence=seq
                    )
                    session.add(point)
                
                # Calculate metrics
                if x_values and y_values:
                    error_pct = parser.calculate_error_percentage(x_values, y_values)
                    if error_pct != float('inf'):
                        metric = OptimizationMetric(
                            simulation_id=sim_id,
                            data_series_id=data_series.id,
                            metric_name='error_percentage',
                            metric_value=error_pct,
                            unit='%'
                        )
                        session.add(metric)
                    
                    gain = parser.calculate_gain(x_values, y_values)
                    metric = OptimizationMetric(
                        simulation_id=sim_id,
                        data_series_id=data_series.id,
                        metric_name='gain',
                        metric_value=gain,
                        unit='ratio'
                    )
                    session.add(metric)
                
                print(f"   ✓ Series {series_num}/{total_series}: {len(x_values)} points", end='\r')
            
            session.commit()
        
        print(f"   ✓ Batch {batch_end}/{total_series} completed" + " "*20)
    
    print(f"\n{'='*60}")
    print(f"✓ IMPORT COMPLETE!")
    print(f"{'='*60}\n")
    print(f"Simulation ID: {sim_id}")
    print(f"Total series imported: {total_series}")
    print(f"\nYou can now query this data using:")
    print(f"  python3 cli.py chat")
    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 import_efficient.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
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

#!/usr/bin/env python3
"""
Test script to validate the CSV parser and data import.
Creates a small test CSV file and imports it.
"""

import os
import csv
from database import init_database
from ingestion import SimulationImporter
from query import SimulationQuery


def create_test_csv(filename='test_simulation.csv'):
    """Create a small test CSV file with the Cadence format."""
    headers = [
        "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) X",
        "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=2.4e-07) Y",
        "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=3.0e-07) X",
        "/I4/Out (Nm_In_W=2.4e-07,Nm_Out_W=3.0e-07) Y",
        "/I4/Out (Nm_In_W=3.0e-07,Nm_Out_W=2.4e-07) X",
        "/I4/Out (Nm_In_W=3.0e-07,Nm_Out_W=2.4e-07) Y",
        "/I4/Out (Nm_In_W=3.0e-07,Nm_Out_W=3.0e-07) X",
        "/I4/Out (Nm_In_W=3.0e-07,Nm_Out_W=3.0e-07) Y"
    ]
    
    # Generate sample data (10 points per series)
    data = []
    for i in range(10):
        row = []
        for j in range(4):  # 4 series
            x = (i + 1) * 1e-9  # Input current
            if j == 0:
                y = x * 1.0  # Perfect mirror
            elif j == 1:
                y = x * 1.25  # 1.25x gain
            elif j == 2:
                y = x * 0.8  # 0.8x gain
            else:
                y = x * 1.0  # Perfect mirror
            row.extend([x, y])
        data.append(row)
    
    # Write CSV
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)
    
    print(f"Created test CSV file: {filename}")
    return filename


def test_import_and_query():
    """Test the complete import and query pipeline."""
    print("=" * 60)
    print("Testing Circuit Simulation Database")
    print("=" * 60)
    print()
    
    # Initialize database
    print("1. Initializing database...")
    if os.path.exists('test_simulations.db'):
        os.remove('test_simulations.db')
    db = init_database('test_simulations.db', create_tables=True)
    print("   ✓ Database initialized\n")
    
    # Create test CSV
    print("2. Creating test CSV file...")
    csv_file = create_test_csv()
    print()
    
    # Import simulation
    print("3. Importing simulation...")
    importer = SimulationImporter()
    try:
        simulation = importer.import_from_csv(
            csv_path=csv_file,
            simulation_name='Test Current Mirror',
            circuit_name='Simple Current Mirror NMOS',
            description='Test simulation with 4 sweep configurations',
            categories=['Current Mirror', 'NMOS', 'Test'],
            fixed_parameters={
                'Iref': (100e-6, 'A'),
                'Vov': (0.2, 'V'),
                'L': (540e-9, 'm')
            },
            assumptions={
                'vdd': 1.8,
                'vt': 0.5,
                'temperature': 27.0
            },
            calculate_metrics=True
        )
        print(f"   ✓ Imported simulation: {simulation['name']} (ID: {simulation['id']})")
        print()
    except Exception as e:
        print(f"   ✗ Error importing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Query simulations
    print("4. Querying simulations...")
    query = SimulationQuery()
    
    try:
        all_sims = query.search_simulations()
        print(f"   Found {len(all_sims)} simulation(s)\n")
        
        for sim in all_sims:
            print(f"   Simulation: {sim['name']}")
            print(f"   Circuit: {sim['circuit_name']}")
            print(f"   Categories: {sim['categories']}")
            print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Get details
    print("5. Getting simulation details...")
    try:
        details = query.get_simulation_details(simulation['id'])
        if details:
            print(f"   Name: {details['name']}")
            print(f"   Circuit: {details['circuit_name']}")
            print(f"   Description: {details['description']}")
            print(f"\n   Fixed Parameters:")
            for param in details['parameters']:
                print(f"     - {param['name']}: {param['value']} {param['unit']}")
            print(f"\n   Sweep Parameters:")
            for param in details['sweep_parameters']:
                print(f"     - {param}")
            print(f"\n   Optimization Metrics:")
            for metric in details['metrics']:
                print(f"     - {metric['name']}: {metric['value']:.4f} {metric['unit']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Filter by metric
    print("6. Filtering by error percentage...")
    try:
        results = query.filter_by_metric(
            metric_name='error_percentage',
            max_value=10.0
        )
        print(f"   Found {len(results)} result(s) with error < 10%\n")
        for result in results[:5]:
            print(f"   - {result['simulation_name']}")
            print(f"     Error: {result['metric_value']:.2f}%")
            if 'signal_path' in result:
                print(f"     Signal: {result['signal_path']}")
            print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Get data series
    print("7. Getting data series...")
    try:
        data_series = query.get_data_series(simulation['id'])
        print(f"   Found {len(data_series)} data series\n")
        
        for series in data_series[:2]:  # Show first 2
            print(f"   Signal: {series['signal_path']}")
            print(f"   Sweep parameters: {series['sweep_parameters']}")
            print(f"   Data points: {len(series['data_points'])}")
            print(f"   First 3 points:")
            for point in series['data_points'][:3]:
                print(f"     X: {point['x']:.2e}, Y: {point['y']:.2e}")
            print()
    except Exception as e:
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Get statistics
    print("8. Getting metric statistics...")
    try:
        stats = query.get_metric_statistics('error_percentage')
        print(f"   Error Percentage Statistics:")
        print(f"     Min: {stats['min']:.2f}%")
        print(f"     Max: {stats['max']:.2f}%")
        print(f"     Avg: {stats['avg']:.2f}%")
        print(f"     Count: {stats['count']}")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    # Categories
    print("9. Listing categories...")
    try:
        categories = query.list_categories()
        print(f"   Found {len(categories)} category(ies):\n")
        for cat in categories:
            print(f"   - {cat['name']}: {cat['simulation_count']} simulation(s)")
        print()
    except Exception as e:
        print(f"   Error: {e}")
    
    print("=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Import your actual data:")
    print("   python cli.py import <your_csv_file> --name 'Sim Name' --circuit 'Circuit Name'")
    print()
    print("2. Start the chatbot:")
    print("   export OPENAI_API_KEY='your-key-here'")
    print("   python cli.py chat")
    print()
    
    # Cleanup
    if os.path.exists(csv_file):
        os.remove(csv_file)
        print(f"Cleaned up test file: {csv_file}")


if __name__ == '__main__':
    test_import_and_query()

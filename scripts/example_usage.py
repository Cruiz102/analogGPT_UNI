#!/usr/bin/env python3
"""
Example usage of the circuit simulation database and query system.

This script demonstrates:
1. Initializing the database
2. Importing simulation data from CSV
3. Querying simulations
4. Filtering by metrics
5. Retrieving data series
"""

from database import init_database
from ingestion import SimulationImporter
from query import SimulationQuery


def main():
    print("=" * 60)
    print("Circuit Simulation Database - Example Usage")
    print("=" * 60)
    print()
    
    # Step 1: Initialize database
    print("1. Initializing database...")
    db = init_database('simulations.db', create_tables=True)
    print("   ✓ Database initialized\n")
    
    # Step 2: Import simulation (commented out for large files)
    print("2. Importing simulation from CSV...")
    print("   Note: The CSV files in this workspace are very large.")
    print("   To import, uncomment the code below and run:\n")
    
    print("   Example import command:")
    print("""
    importer = SimulationImporter()
    simulation = importer.import_from_csv(
        csv_path='Bode_Plot_SimpleCurrentMirror_Nmos_(RL&CL).csv',
        simulation_name='Current Mirror W Sweep - Bode Analysis',
        circuit_name='Simple Current Mirror NMOS',
        description='Parametric sweep of input and output widths with RL and CL',
        categories=['Current Mirror', 'NMOS', 'Bode Plot', 'Parametric Sweep'],
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
    print(f"   ✓ Imported simulation: {simulation.name} (ID: {simulation.id})")
    """)
    print()
    
    # Step 3: Query simulations
    print("3. Querying simulations...")
    query = SimulationQuery()
    
    try:
        # Search all simulations
        all_sims = query.search_simulations()
        print(f"   Found {len(all_sims)} simulation(s) in database")
        
        if all_sims:
            print("\n   Simulations:")
            for sim in all_sims[:5]:  # Show first 5
                print(f"   - [{sim.id}] {sim.name}")
                print(f"     Circuit: {sim.circuit_name}")
                if sim.description:
                    print(f"     Description: {sim.description[:60]}...")
                print()
        else:
            print("   No simulations found. Import data first using:")
            print("   python cli.py import <csv_file> --name <name> --circuit <circuit>")
        
    except Exception as e:
        print(f"   Error querying simulations: {e}")
    
    print()
    
    # Step 4: Filter by metrics
    print("4. Filtering by optimization metrics...")
    print("   Example: Find simulations with low error percentage\n")
    
    print("   Example query:")
    print("""
    low_error = query.filter_by_metric(
        metric_name='error_percentage',
        max_value=5.0,
        limit=10
    )
    
    for result in low_error:
        print(f"Simulation: {result['simulation_name']}")
        print(f"  Error: {result['metric_value']:.2f}%")
    """)
    print()
    
    # Step 5: Get simulation details
    print("5. Getting simulation details...")
    print("   Example for simulation ID 1:\n")
    
    print("   Example query:")
    print("""
    details = query.get_simulation_details(1)
    
    if details:
        print(f"Name: {details['name']}")
        print(f"Circuit: {details['circuit_name']}")
        print(f"Parameters:")
        for param in details['parameters']:
            print(f"  - {param['name']}: {param['value']} {param['unit']}")
        print(f"Metrics:")
        for metric in details['metrics']:
            print(f"  - {metric['name']}: {metric['value']} {metric['unit']}")
    """)
    print()
    
    # Step 6: Get data series
    print("6. Retrieving data series...")
    print("   Example: Get data for specific sweep parameters\n")
    
    print("   Example query:")
    print("""
    data_series = query.get_data_series(
        simulation_id=1,
        signal_path='/I4/Out',
        sweep_filters={'Nm_In_W': 2.4e-07, 'Nm_Out_W': 2.4e-07}
    )
    
    for series in data_series:
        print(f"Signal: {series['signal_path']}")
        print(f"Sweep params: {series['sweep_parameters']}")
        print(f"Data points: {len(series['data_points'])}")
        
        # Plot or analyze data points
        for point in series['data_points'][:5]:  # First 5 points
            print(f"  X: {point['x']}, Y: {point['y']}")
    """)
    print()
    
    # Step 7: Get statistics
    print("7. Getting metric statistics...")
    print("   Example: Get error percentage statistics\n")
    
    print("   Example query:")
    print("""
    stats = query.get_metric_statistics('error_percentage')
    
    print(f"Error Percentage Statistics:")
    print(f"  Min: {stats['min']:.2f}%")
    print(f"  Max: {stats['max']:.2f}%")
    print(f"  Avg: {stats['avg']:.2f}%")
    print(f"  Count: {stats['count']}")
    """)
    print()
    
    # Step 8: List categories
    print("8. Listing categories...")
    try:
        categories = query.list_categories()
        if categories:
            print(f"   Found {len(categories)} category(ies):\n")
            for cat in categories:
                print(f"   - {cat['name']}: {cat['simulation_count']} simulation(s)")
                if cat['description']:
                    print(f"     {cat['description']}")
        else:
            print("   No categories found yet.")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("To use this system:")
    print()
    print("1. Import your simulation data:")
    print("   python cli.py import data.csv --name 'My Sim' --circuit 'Current Mirror'")
    print()
    print("2. Start the chatbot:")
    print("   python cli.py chat")
    print()
    print("3. Ask questions like:")
    print("   - 'Show me all current mirror simulations'")
    print("   - 'Find simulations with error less than 5%'")
    print("   - 'What are the parameters for simulation 1?'")
    print("   - 'Get data for simulation 1 where Nm_In_W is 2.4e-07'")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()

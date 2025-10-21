#!/usr/bin/env python3
"""
Command-line interface for the Circuit Simulation Chatbot.
"""
import argparse
import os
import sys
from getpass import getpass

from database import init_database
from ingestion import SimulationImporter
from chatbot import CircuitChatbot


def import_simulation(args):
    """Import a simulation from CSV."""
    print(f"Importing simulation from {args.csv_file}...")
    
    # Initialize database
    init_database(args.database)
    
    # Parse fixed parameters
    fixed_params = {}
    if args.parameters:
        for param in args.parameters:
            try:
                name, value, unit = param.split(':')
                fixed_params[name] = (float(value), unit)
            except ValueError:
                print(f"Warning: Invalid parameter format '{param}'. Expected 'name:value:unit'")
    
    # Parse assumptions
    assumptions = {}
    if args.vdd:
        assumptions['vdd'] = args.vdd
    if args.vt:
        assumptions['vt'] = args.vt
    if args.temperature:
        assumptions['temperature'] = args.temperature
    
    # Import simulation
    importer = SimulationImporter()
    try:
        simulation = importer.import_from_csv(
            csv_path=args.csv_file,
            simulation_name=args.name,
            circuit_name=args.circuit,
            description=args.description or "",
            categories=args.categories,
            fixed_parameters=fixed_params,
            assumptions=assumptions,
            calculate_metrics=not args.no_metrics
        )
        print(f"✓ Successfully imported simulation '{simulation['name']}' (ID: {simulation['id']})")
    except Exception as e:
        print(f"✗ Error importing simulation: {e}")
        sys.exit(1)


def run_chatbot(args):
    """Run the interactive chatbot."""
    # Get API key
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        api_key = getpass("Enter your OpenAI API key: ")
    
    if not api_key:
        print("Error: OpenAI API key is required")
        sys.exit(1)
    
    # Initialize database
    init_database(args.database)
    
    # Initialize chatbot
    print("Initializing chatbot...")
    try:
        chatbot = CircuitChatbot(api_key=api_key, model=args.model)
        print("✓ Chatbot ready!\n")
    except Exception as e:
        print(f"✗ Error initializing chatbot: {e}")
        sys.exit(1)
    
    # Interactive loop
    print("Circuit Simulation Chatbot")
    print("=" * 50)
    print("Ask questions about your circuit simulations.")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("Type 'reset' to start a new conversation.")
    print("=" * 50)
    print()
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                chatbot.reset_conversation()
                print("Conversation reset.\n")
                continue
            
            # Get response
            print("Assistant: ", end="", flush=True)
            response = chatbot.chat(user_input)
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Circuit Simulation Database and Chatbot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--database',
        default='simulations.db',
        help='Path to SQLite database file (default: simulations.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import simulation from CSV')
    import_parser.add_argument('csv_file', help='Path to CSV file')
    import_parser.add_argument('--name', required=True, help='Simulation name')
    import_parser.add_argument('--circuit', required=True, help='Circuit name')
    import_parser.add_argument('--description', help='Simulation description')
    import_parser.add_argument('--categories', nargs='+', help='Categories to assign')
    import_parser.add_argument(
        '--parameters',
        nargs='+',
        help='Fixed parameters in format name:value:unit (e.g., Iref:100e-6:A)'
    )
    import_parser.add_argument('--vdd', type=float, help='Supply voltage (V)')
    import_parser.add_argument('--vt', type=float, help='Threshold voltage (V)')
    import_parser.add_argument('--temperature', type=float, help='Temperature (C)')
    import_parser.add_argument('--no-metrics', action='store_true', help='Skip metric calculation')
    import_parser.set_defaults(func=import_simulation)
    
    # Chat command
    chat_parser = subparsers.add_parser('chat', help='Run interactive chatbot')
    chat_parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    chat_parser.add_argument('--model', default='gpt-4-turbo-preview', help='OpenAI model')
    chat_parser.set_defaults(func=run_chatbot)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    args.func(args)


if __name__ == '__main__':
    main()

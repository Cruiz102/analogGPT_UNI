#!/usr/bin/env python3
"""
OpenAI Assistant for Query Database
Uses OpenAI's function calling API to interact with the sweep database naturally.
"""
import os
import json
import sys
from typing import List, Dict, Any, Optional
import openai
from query_database import SweepDB, ErrorAnalyzer, parse_params_string

class QueryDatabaseTools:
    """
    Tools for OpenAI function calling to interact with the sweep database.
    """
    
    def __init__(self, db: SweepDB):
        self.db = db
        self.analyzer = ErrorAnalyzer(db)
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Get the tools definition for OpenAI function calling.
        
        Returns:
            List of tool definitions for OpenAI API
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_all_series",
                    "description": "List all available parameter series in the database. Returns a list of indices and their parameters.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of series to return (optional)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "show_series",
                    "description": "Show detailed information about a specific parameter series including sample data points.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the series to show"
                            },
                            "sample": {
                                "type": "integer",
                                "description": "Number of sample data points to display (default: 10)"
                            }
                        },
                        "required": ["index"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_value",
                    "description": "Query the closest Y value for a given X value in a specific parameter series. Use this when the user asks 'what is Y when X is...' or similar queries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the series to query"
                            },
                            "params": {
                                "type": "string",
                                "description": "Parameter string like 'Nm_In_W=3.60116e-06, Nm_Out_W=3.9271e-07'"
                            },
                            "x": {
                                "type": "number",
                                "description": "X value to query"
                            }
                        },
                        "required": ["x"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "calculate_error",
                    "description": "Calculate error statistics for a specific parameter series. Shows min, max, mean absolute and percentage errors.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {
                                "type": "integer",
                                "description": "Index of the series"
                            },
                            "params": {
                                "type": "string",
                                "description": "Parameter string like 'Nm_In_W=3.60116e-06, Nm_Out_W=3.9271e-07'"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "find_minimum_error",
                    "description": "Find the parameter combination that has the minimum error across all series. Use when user asks 'what parameters give the best accuracy' or 'which parameters have lowest error'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "use_percentage": {
                                "type": "boolean",
                                "description": "Whether to use percentage error instead of absolute error (default: false)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_by_error_threshold",
                    "description": "Find all parameter series that meet an error threshold criteria. Use when user asks 'which parameters have error less than X' or 'show me all series with error below Y'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "threshold": {
                                "type": "number",
                                "description": "Error threshold value"
                            },
                            "use_percentage": {
                                "type": "boolean",
                                "description": "Whether to use percentage error (default: false)"
                            },
                            "operator": {
                                "type": "string",
                                "enum": ["<=", "<", ">=", ">", "=="],
                                "description": "Comparison operator (default: <=)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return"
                            }
                        },
                        "required": ["threshold"]
                    }
                }
            }
        ]
    
    def list_all_series(self, limit: Optional[int] = None) -> str:
        """List all parameter series"""
        series_list = self.db.list_series(limit)
        if not series_list:
            return "No series available."
        
        lines = []
        for idx, params in series_list:
            params_str = ", ".join(f"{k}={v:g}" for k, v in params)
            lines.append(f"{idx}: {params_str}")
        
        return "\n".join(lines)
    
    def show_series(self, index: int, sample: int = 10) -> str:
        """Show detailed information about a series"""
        if index < 0 or index >= len(self.db.params_for_index):
            return f"Error: Index {index} out of range (0-{len(self.db.params_for_index)-1})"
        
        params = self.db.params_for_index[index]
        sd = self.db.series_by_params[params]
        
        lines = [
            f"Series Index: {index}",
            f"Parameters: {', '.join(f'{k}={v:g}' for k, v in params)}",
            f"Data Points: {sd.x.size}",
            "",
            f"Sample (first {min(sample, sd.x.size)} points):"
        ]
        
        n = min(sample, sd.x.size)
        for i in range(n):
            lines.append(f"  x={sd.x[i]:.6e}, y={sd.y[i]:.6e}")
        
        return "\n".join(lines)
    
    def query_value(self, x: float, index: Optional[int] = None, params: Optional[str] = None) -> str:
        """Query closest Y value for given X"""
        try:
            if index is not None:
                xf, yf, i, p = self.db.query_closest_y(series_index=index, x_query=x)
            elif params is not None:
                p = parse_params_string(params)
                xf, yf, i, p = self.db.query_closest_y(params=p, x_query=x)
            else:
                return "Error: Must provide either 'index' or 'params'"
            
            result = {
                "x_query": x,
                "x_found": xf,
                "y_found": yf,
                "row": i,
                "params": {k: v for k, v in p}
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def calculate_error(self, index: Optional[int] = None, params: Optional[str] = None) -> str:
        """Calculate error statistics for a series"""
        try:
            if index is not None:
                if index < 0 or index >= len(self.db.params_for_index):
                    return f"Error: Index {index} out of range"
                p = self.db.params_for_index[index]
            elif params is not None:
                p = parse_params_string(params)
            else:
                return "Error: Must provide either 'index' or 'params'"
            
            stats = self.analyzer.calculate_series_error(p)
            
            lines = [
                f"Parameters: {', '.join(f'{k}={v:g}' for k, v in p)}",
                "",
                f"Minimum Absolute Error: {stats['min_error']:.6e}",
                f"  at x={stats['min_error_x']:.6e}, y={stats['min_error_y']:.6e}",
                "",
                f"Minimum Percentage Error: {stats['min_pct_error']:.6f}%",
                f"  at x={stats['min_pct_error_x']:.6e}, y={stats['min_pct_error_y']:.6e}",
                "",
                f"Mean Absolute Error: {stats['mean_error']:.6e}",
                f"Mean Percentage Error: {stats['mean_pct_error']:.6f}%",
                f"Max Absolute Error: {stats['max_error']:.6e}"
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def find_minimum_error(self, use_percentage: bool = False) -> str:
        """Find parameters with minimum error"""
        try:
            metric = "min_pct_error" if use_percentage else "min_error"
            best_params, stats = self.analyzer.find_min_error_params(metric)
            
            lines = [
                "Best Parameters Found:",
                f"  {', '.join(f'{k}={v:g}' for k, v in best_params)}",
                "",
                f"Minimum Absolute Error: {stats['min_error']:.6e}",
                f"  at x={stats['min_error_x']:.6e}, y={stats['min_error_y']:.6e}",
                "",
                f"Minimum Percentage Error: {stats['min_pct_error']:.6f}%",
                f"  at x={stats['min_pct_error_x']:.6e}, y={stats['min_pct_error_y']:.6e}",
                "",
                f"Mean Absolute Error: {stats['mean_error']:.6e}",
                f"Mean Percentage Error: {stats['mean_pct_error']:.6f}%"
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def filter_by_error_threshold(self, threshold: float, use_percentage: bool = False,
                                   operator: str = "<=", limit: Optional[int] = None) -> str:
        """Filter series by error threshold"""
        try:
            metric = "min_pct_error" if use_percentage else "min_error"
            results = self.analyzer.filter_by_error_threshold(threshold, metric, operator)
            
            error_type = "percentage" if use_percentage else "absolute"
            lines = [
                f"Found {len(results)} series where {error_type} error {operator} {threshold}",
                ""
            ]
            
            display_limit = limit if limit is not None else len(results)
            for i, (params, stats) in enumerate(results[:display_limit], 1):
                params_str = ", ".join(f"{k}={v:g}" for k, v in params)
                lines.append(f"{i}. {params_str}")
                lines.append(f"   Min Error: {stats['min_error']:.6e}, Min % Error: {stats['min_pct_error']:.6f}%")
            
            if len(results) > display_limit:
                lines.append(f"\n... and {len(results) - display_limit} more")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a function by name with given arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Dictionary of function arguments
            
        Returns:
            Result as a string
        """
        if function_name == "list_all_series":
            return self.list_all_series(**arguments)
        elif function_name == "show_series":
            return self.show_series(**arguments)
        elif function_name == "query_value":
            return self.query_value(**arguments)
        elif function_name == "calculate_error":
            return self.calculate_error(**arguments)
        elif function_name == "find_minimum_error":
            return self.find_minimum_error(**arguments)
        elif function_name == "filter_by_error_threshold":
            return self.filter_by_error_threshold(**arguments)
        else:
            return f"Error: Unknown function '{function_name}'"


class OpenAIQueryAssistant:
    """
    OpenAI assistant for natural language interaction with the sweep database.
    """
    
    def __init__(self, db: SweepDB, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """
        Initialize the assistant.
        
        Args:
            db: SweepDB instance
            api_key: OpenAI API key (if None, tries: 1) key file, 2) OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o)
        """
        self.db = db
        self.tools = QueryDatabaseTools(db)
        self.model = model
        
        # Set up OpenAI client
        if api_key:
            openai.api_key = api_key
        else:
            # Try reading from key file first
            key_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "key")
            if os.path.exists(key_file_path):
                try:
                    with open(key_file_path, 'r') as f:
                        openai.api_key = f.read().strip()
                except Exception as e:
                    print(f"Warning: Could not read key file: {e}", file=sys.stderr)
                    openai.api_key = None
            else:
                openai.api_key = None
            
            # Fall back to environment variable
            if not openai.api_key:
                openai.api_key = os.getenv("OPENAI_API_KEY")
            
            if not openai.api_key:
                raise ValueError("OpenAI API key not found. Place it in 'key' file, set OPENAI_API_KEY env variable, or pass api_key parameter.")
        
        self.client = openai.OpenAI(api_key=openai.api_key)
        
        # Conversation history
        self.messages: List[Dict[str, Any]] = [
            {
                "role": "system",
                "content": """You are a helpful assistant for analyzing circuit simulation sweep data.
                
The database contains parameter sweep simulations with different values of Nm_In_W and Nm_Out_W.
Each series has X and Y data points where the error is calculated as |Y - X|.

You can help users:
- List and explore available parameter series
- Query specific data points
- Calculate error statistics
- Find optimal parameters with minimum error
- Filter series by error thresholds

Always provide clear, concise answers and use the appropriate tools to answer questions."""
            }
        ]
    
    def chat(self, user_message: str, verbose: bool = False) -> str:
        """
        Send a message and get a response.
        
        Args:
            user_message: User's question or request
            verbose: Whether to print detailed information about tool calls
            
        Returns:
            Assistant's response
        """
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": user_message
        })
        
        if verbose:
            print(f"\n🤔 User: {user_message}\n")
        
        # Get response from OpenAI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self.tools.get_tools_definition(),
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # If no tool calls, return the message directly
        if not tool_calls:
            assistant_message = response_message.content
            self.messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            return assistant_message
        
        # Execute tool calls
        self.messages.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if verbose:
                print(f"🔧 Calling function: {function_name}")
                print(f"   Arguments: {json.dumps(function_args, indent=2)}\n")
            
            # Execute the function
            function_response = self.tools.execute_function(function_name, function_args)
            
            if verbose:
                print(f"📊 Function result:\n{function_response}\n")
            
            # Add function response to messages
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response
            })
        
        # Get final response with function results
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages
        )
        
        assistant_message = final_response.choices[0].message.content
        self.messages.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.messages = self.messages[:1]  # Keep only system message


def main():
    """Interactive chat interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Assistant for Sweep Database")
    parser.add_argument("csv", help="Path to CSV file")
    parser.add_argument("--model", default="gpt-4o", help="OpenAI model to use")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show tool calls and results")
    parser.add_argument("--low-memory", action="store_true", help="Use low memory mode for CSV parsing")
    args = parser.parse_args()
    
    # Load database
    print("Loading database...")
    try:
        db = SweepDB.from_csv(args.csv, low_memory=args.low_memory)
        print(f"✓ Loaded {len(db.params_for_index)} parameter series\n")
    except Exception as e:
        print(f"Error loading database: {e}")
        return
    
    # Initialize assistant
    try:
        assistant = OpenAIQueryAssistant(db, model=args.model)
        print(f"✓ Connected to OpenAI ({args.model})\n")
    except Exception as e:
        print(f"Error initializing OpenAI: {e}")
        print("Make sure OPENAI_API_KEY environment variable is set.")
        return
    
    print("=== Sweep Database AI Assistant ===")
    print("Ask me anything about the simulation data!")
    print("Commands: 'exit', 'quit', 'reset' (clear conversation)")
    print("=" * 40 + "\n")
    
    # Chat loop
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!")
                break
            
            if user_input.lower() == "reset":
                assistant.reset_conversation()
                print("\n✓ Conversation reset\n")
                continue
            
            # Get response
            response = assistant.chat(user_input, verbose=args.verbose)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()

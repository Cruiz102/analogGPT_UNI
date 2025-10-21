"""
OpenAI API integration with function calling for database queries.
"""
import json
from typing import List, Dict, Any, Optional
import openai

from query import SimulationQuery
from ingestion import SimulationImporter


class ChatbotTools:
    """
    Define tools (functions) available to the OpenAI chatbot.
    """
    
    def __init__(self):
        """Initialize tools with query interface."""
        self.query = SimulationQuery()
        self.importer = SimulationImporter()
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Get the tools definition for OpenAI function calling.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_simulations",
                    "description": "Search for circuit simulations by name, circuit name, or categories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Simulation name (partial match)"
                            },
                            "circuit_name": {
                                "type": "string",
                                "description": "Circuit name (partial match), e.g., 'Current Mirror', 'OpAmp'"
                            },
                            "categories": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of category names to filter by"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "filter_by_metric",
                    "description": "Filter simulations by optimization metric values like error percentage, gain, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric_name": {
                                "type": "string",
                                "description": "Name of the metric (e.g., 'error_percentage', 'gain')"
                            },
                            "min_value": {
                                "type": "number",
                                "description": "Minimum metric value (inclusive)"
                            },
                            "max_value": {
                                "type": "number",
                                "description": "Maximum metric value (inclusive)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results"
                            }
                        },
                        "required": ["metric_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_simulation_details",
                    "description": "Get detailed information about a specific simulation including parameters, metrics, and categories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "integer",
                                "description": "The ID of the simulation"
                            }
                        },
                        "required": ["simulation_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_data_series",
                    "description": "Get data series (X,Y data points) for a simulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "simulation_id": {
                                "type": "integer",
                                "description": "The ID of the simulation"
                            },
                            "signal_path": {
                                "type": "string",
                                "description": "Optional signal path filter (e.g., '/I4/Out')"
                            },
                            "sweep_filters": {
                                "type": "object",
                                "description": "Optional sweep parameter filters (e.g., {'Nm_In_W': 2.4e-07})"
                            }
                        },
                        "required": ["simulation_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_categories",
                    "description": "List all available simulation categories with counts",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_metric_statistics",
                    "description": "Get statistics (min, max, avg) for a metric across simulations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "metric_name": {
                                "type": "string",
                                "description": "Name of the metric"
                            },
                            "circuit_name": {
                                "type": "string",
                                "description": "Optional circuit name filter"
                            }
                        },
                        "required": ["metric_name"]
                    }
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Execute a tool function and return the result as JSON.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Dictionary of arguments for the tool
            
        Returns:
            JSON string with the result
        """
        try:
            if tool_name == "search_simulations":
                results = self.query.search_simulations(**arguments)
                return json.dumps(results, indent=2)
            
            elif tool_name == "filter_by_metric":
                results = self.query.filter_by_metric(**arguments)
                return json.dumps(results, indent=2)
            
            elif tool_name == "get_simulation_details":
                result = self.query.get_simulation_details(**arguments)
                if result is None:
                    return json.dumps({"error": "Simulation not found"})
                return json.dumps(result, indent=2)
            
            elif tool_name == "get_data_series":
                results = self.query.get_data_series(**arguments)
                return json.dumps(results, indent=2)
            
            elif tool_name == "list_categories":
                results = self.query.list_categories()
                return json.dumps(results, indent=2)
            
            elif tool_name == "get_metric_statistics":
                result = self.query.get_metric_statistics(**arguments)
                return json.dumps(result, indent=2)
            
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        except Exception as e:
            return json.dumps({"error": str(e)})


class CircuitChatbot:
    """
    Chatbot interface for querying circuit simulation database.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        """
        Initialize chatbot.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.tools = ChatbotTools()
        self.conversation_history = []
    
    def chat(self, user_message: str) -> str:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            user_message: User's message
            
        Returns:
            Chatbot's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Initial API call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant for querying circuit simulation data. "
                        "You have access to a database of Cadence circuit simulations, including "
                        "current mirrors, op-amps, and other circuits. You can search simulations, "
                        "filter by metrics like error percentage and gain, and retrieve detailed "
                        "simulation data. Always be precise and helpful in your responses."
                    )
                }
            ] + self.conversation_history,
            tools=self.tools.get_tools_definition(),
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # If no tool calls, return the response
        if not tool_calls:
            assistant_message = response_message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            return assistant_message
        
        # Process tool calls
        self.conversation_history.append(response_message)
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the tool
            function_response = self.tools.execute_tool(function_name, function_args)
            
            # Add tool response to history
            self.conversation_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": function_response
            })
        
        # Get final response from the model
        second_response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant for querying circuit simulation data. "
                        "You have access to a database of Cadence circuit simulations, including "
                        "current mirrors, op-amps, and other circuits. You can search simulations, "
                        "filter by metrics like error percentage and gain, and retrieve detailed "
                        "simulation data. Always be precise and helpful in your responses."
                    )
                }
            ] + self.conversation_history
        )
        
        assistant_message = second_response.choices[0].message.content
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })
        
        return assistant_message
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

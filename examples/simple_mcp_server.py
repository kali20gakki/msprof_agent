#!/usr/bin/env python3
"""Simple example MCP server for MSProf Agent.

This is a simple MCP server that provides basic calculator tools.
To use with MSProf Agent:

    msprof mcp add --name calculator --command python --args "/path/to/simple_mcp_server.py"

"""

import json
import sys
from typing import Any


def send_message(message: dict[str, Any]) -> None:
    """Send a JSON-RPC message."""
    print(json.dumps(message), flush=True)


def handle_initialize(message: dict[str, Any]) -> None:
    """Handle initialize request."""
    response = {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "simple-calculator",
                "version": "0.1.0"
            }
        }
    }
    send_message(response)


def handle_tools_list(message: dict[str, Any]) -> None:
    """Handle tools/list request."""
    response = {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "tools": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "subtract",
                    "description": "Subtract two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "multiply",
                    "description": "Multiply two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"}
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "divide",
                    "description": "Divide two numbers",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "Dividend"},
                            "b": {"type": "number", "description": "Divisor"}
                        },
                        "required": ["a", "b"]
                    }
                }
            ]
        }
    }
    send_message(response)


def handle_tools_call(message: dict[str, Any]) -> None:
    """Handle tools/call request."""
    params = message["params"]
    tool_name = params["name"]
    arguments = params["arguments"]
    
    result = ""
    
    try:
        if tool_name == "add":
            result = str(arguments["a"] + arguments["b"])
        elif tool_name == "subtract":
            result = str(arguments["a"] - arguments["b"])
        elif tool_name == "multiply":
            result = str(arguments["a"] * arguments["b"])
        elif tool_name == "divide":
            if arguments["b"] == 0:
                result = "Error: Division by zero"
            else:
                result = str(arguments["a"] / arguments["b"])
        else:
            result = f"Unknown tool: {tool_name}"
    except Exception as e:
        result = f"Error: {e}"
    
    response = {
        "jsonrpc": "2.0",
        "id": message["id"],
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ],
            "isError": False
        }
    }
    send_message(response)


def main() -> None:
    """Main entry point."""
    while True:
        try:
            line = input()
            if not line:
                continue
            
            message = json.loads(line)
            method = message.get("method", "")
            
            if method == "initialize":
                handle_initialize(message)
            elif method == "tools/list":
                handle_tools_list(message)
            elif method == "tools/call":
                handle_tools_call(message)
            elif method == "notifications/initialized":
                # No response needed for notifications
                pass
            else:
                # Unknown method
                send_message({
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                })
        
        except EOFError:
            break
        except json.JSONDecodeError as e:
            send_message({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {e}"
                }
            })
        except Exception as e:
            send_message({
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {e}"
                }
            })


if __name__ == "__main__":
    main()

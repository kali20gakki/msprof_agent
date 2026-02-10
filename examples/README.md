# MSProf Agent Examples

This directory contains example files for MSProf Agent.

## Simple MCP Server

`simple_mcp_server.py` - A basic calculator MCP server demonstrating how to create custom MCP tools.

### Features

- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract two numbers
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers

### Usage

1. Add the server to MSProf Agent:

```bash
msprof mcp add --name calculator --command python --args "/path/to/simple_mcp_server.py"
```

2. Start chatting:

```bash
msprof chat
```

3. Ask the agent to use the calculator:

```
What is 123 + 456?
```

The agent will automatically use the `add` tool from the calculator MCP server.

## Official MCP Servers

You can also use official MCP servers from the community:

### Filesystem Server

```bash
msprof mcp add --name filesystem --command npx --args "-y,@modelcontextprotocol/server-filesystem,/path/to/directory"
```

### SQLite Server

```bash
msprof mcp add --name sqlite --command npx --args "-y,@modelcontextprotocol/server-sqlite,/path/to/database.db"
```

### Git Server

```bash
msprof mcp add --name git --command uvx --args "mcp-server-git"
```

## Creating Your Own MCP Server

To create your own MCP server:

1. Implement the MCP protocol (JSON-RPC over stdio)
2. Handle these methods:
   - `initialize` - Server initialization
   - `tools/list` - List available tools
   - `tools/call` - Execute a tool
3. Return results in the MCP format

See `simple_mcp_server.py` for a complete example.

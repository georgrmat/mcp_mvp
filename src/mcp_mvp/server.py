from mcp.server.fastmcp import FastMCP
from tools import register_tools

mcp = FastMCP("mcp-mvp")
register_tools(mcp)

if __name__ == "__main__":
    mcp.run()

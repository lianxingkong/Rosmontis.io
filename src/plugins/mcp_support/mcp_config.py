from .MultiMCPManager import McpServerConfig

mcp_configs = [
    McpServerConfig(
        name="filesystem",
        transport="stdio",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "./mcp_workdir/fs"],
        prefix="fs",
        timeout=60
    )
]
"""
其他例子
    McpServerConfig(
        name="local_python",
        transport="stdio",
        command="python",
        args=["/path/to/local_mcp_server.py"],
        env={"API_KEY": "secret_123"},
        prefix="local",
        timeout=30
    )
    McpServerConfig(
        name="database",
        transport="streamable-http",
        url="http://internal:9000/mcp",
        prefix="db",
        timeout=60,
        headers={"X-API-Key": "secret"}
    )
    McpServerConfig(
        name="search",
        transport="sse",
        url="http://internal:8080/sse",
        prefix="search",
        timeout=30
    )
"""

import asyncio
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client
from nonebot.log import logger


@dataclass
class McpServerConfig:
    """MCP 服务器配置"""
    name: str  # 唯一, 必须
    transport: Literal["stdio", "sse", "streamable-http"] = "stdio"
    # 通信方案

    # stdio config
    command: Optional[str] = None  # 必须
    args: Optional[list] = None
    env: Optional[Dict[str, str]] = None

    # SSE / Streamable HTTP config
    url: Optional[str] = None  # 必须

    # 通用配置
    timeout: int = 30
    prefix: Optional[str] = None
    # 私有前缀, 用于区分同名工具
    headers: Optional[Dict[str, str]] = None  # 认证头等


class MultiMCPManager:
    def __init__(self, configs: list[McpServerConfig]):
        self.configs = configs
        self.sessions: Dict[str, ClientSession] = {}  # 保存会话
        self.tool_map: Dict[str, str] = {}  # 工具聚合的列表
        self.tool_original_map: Dict[str, str] = {}  # 修饰后的名称-修饰前的名称
        self.all_tools: list = []  # 工具的列表
        self._contexts: list = []  # 句柄列表,清理用
        # self._stop_event = asyncio.Event() # 关闭事件

    async def connect_all(self):
        """ 初始化所有mcp连接 """
        tasks = [self._connect_single(cfg) for cfg in self.configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for cfg, result in zip(self.configs, results):
            if isinstance(result, Exception):
                logger.warning(f"server: {cfg.name} connected failed")
            else:
                logger.info(f"server: {cfg.name} connected")
        await self.refresh_tools()

    async def _connect_single(self, cfg: McpServerConfig):
        """ 处理单个连接 """
        transport = await self._create_transport(cfg)
        await self._init_session(cfg.name, transport)
        return True

    async def _create_transport(self, cfg: McpServerConfig) -> AbstractAsyncContextManager:
        """ 根据配置创建对应的 transport """
        if cfg.transport == "stdio":
            if not cfg.command:
                raise ValueError(f"stdio '{cfg.name}'need command")
            server_params = StdioServerParameters(
                command=cfg.command,
                args=cfg.args or [],
                env=cfg.env
            )
            return stdio_client(server_params)
        elif cfg.transport == "sse":
            if not cfg.url:
                raise ValueError(f"sse '{cfg.name}'need url")
            return sse_client(cfg.url, timeout=cfg.timeout)
        elif cfg.transport == "streamable-http":
            if not cfg.url:
                raise ValueError(f"streamable-http '{cfg.name}'need url")
            return streamable_http_client(
                url=cfg.url,
                timeout=cfg.timeout,
                headers=cfg.headers or {}
            )
        else:
            raise ValueError(f"transport {cfg.transport} not supported")

    async def _init_session(self, name: str, transport: AbstractAsyncContextManager):
        """ 通用 session 初始化 """
        read, write = await transport.__aenter__()
        self._contexts.append(transport)

        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()

        self.sessions[name] = session
        logger.info(f"Session {name} initialized")

    def _reset_tool_data(self):
        self.all_tools.clear()
        self.tool_map.clear()
        self.tool_original_map.clear()

    async def refresh_tools(self):
        """ 获取全部工具, 维护映射 """
        self._reset_tool_data()
        for name, session in self.sessions.items():
            # name: MCP 名称
            cfg = next((c for c in self.configs if c.name == name), None)
            prefix = cfg.prefix if cfg else name
            try:
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    original_name = tool.name  # 原始名称
                    prefixed_name = f"{prefix}_{original_name}"  #
                    if prefixed_name in self.tool_map:
                        logger.warning(f"tool {prefixed_name} already used")
                        prefixed_name = f"{name}_{prefix}_{original_name}"

                    self.tool_original_map[prefixed_name] = original_name
                    # 修正名称: 原始名称
                    self.tool_map[prefixed_name] = name
                    # 修正名称: MCP服务名

                    self.all_tools.append({
                        "type": "function",
                        "function": {
                            "name": prefixed_name,
                            "description": f"[{original_name}] {tool.description}",
                            "parameters": tool.inputSchema
                        }
                    })
                    logger.debug(f"tool {prefixed_name} added")

            except Exception as e:
                logger.warning(f"server {name} failed to get tools: {e}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """ 调用工具 """
        server_name = self.tool_map.get(tool_name)
        original_name = self.tool_original_map.get(tool_name)
        if server_name is None or original_name is None:
            raise ValueError(f"tool {tool_name} not registered")

        logger.debug(f"tool: {server_name} : {original_name} called")
        session = self.sessions[server_name]  # 获取 ClientSession

        _text = ""
        result = await session.call_tool(name=original_name, arguments=arguments)
        if hasattr(result, 'content') and result.content:
            _text = "\n".join(
                item.text if hasattr(item, 'text') else str(item)
                for item in result.content
            )
        return _text or "执行成功但无输出"

    async def close_all(self):
        """ 关闭所有连接 """
        for ctx in self._contexts:
            try:
                await ctx.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"server failed to close context: {e}")

    def get_status(self) -> Dict[str, Any]:
        """ MCP 状态 """
        return {
            "connected_servers": list(self.sessions.keys()),
            "all_tools": len(self.tool_map),
            "transport_summary": {
                cfg.name: cfg.transport for cfg in self.configs
            }
        }

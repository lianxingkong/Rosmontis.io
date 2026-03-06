from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="aiAgents",
    description="处理agents调用",
    usage="",
    config=Config,
)

_config = get_plugin_config(Config)
config = _config.aiagents

if config.is_enable:
    from .tool_dicts import *
    from .tool_funcs import *
    from .tool_handle import *

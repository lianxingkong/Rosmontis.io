from nonebot import get_driver
from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="mcp_support",
    description="",
    usage="",
    config=Config,
)

_config = get_plugin_config(Config)
config = _config.mcpsupport
driver = get_driver()

from .MultiMCPManager import MultiMCPManager
from .mcp_config import mcp_configs

if config.is_enable:
    mcp_manger = MultiMCPManager(mcp_configs)
else:
    mcp_manger = None


@driver.on_startup
async def _init_mcp_support():
    if config.is_enable:
        await mcp_manger.connect_all()


@driver.on_shutdown
async def _shutdown_mcp_support():
    if config.is_enable:
        await mcp_manger.close_all()

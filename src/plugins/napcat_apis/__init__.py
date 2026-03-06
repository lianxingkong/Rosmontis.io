from nonebot import get_plugin_config
from nonebot.plugin import PluginMetadata

from .config import Config

__plugin_meta__ = PluginMetadata(
    name="napcat_apis",
    description="",
    usage="",
    config=Config,
)

_config = get_plugin_config(Config)
config = _config.napcatapi

if config.is_enable:
    from .napcatqq_upload_stream import OneBotUploadTester

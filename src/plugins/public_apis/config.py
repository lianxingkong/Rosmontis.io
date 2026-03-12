from pydantic import BaseModel


class ScopedConfig(BaseModel):
    """Plugin Config Here"""
    upload_ws_url: str  # 上传 url
    upload_ws_token: str  # token


class Config(BaseModel):
    """Plugin Config Here"""
    publicapi: ScopedConfig

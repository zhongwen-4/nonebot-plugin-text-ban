from pydantic import BaseModel
from nonebot import get_plugin_config

class Config(BaseModel):
    strict: bool = False
    pinyin: bool = False
    ocr: bool = False
    kick: bool = False

plugin_config = get_plugin_config(config= Config)
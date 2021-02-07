from pydantic import BaseSettings, Field
from functools import lru_cache
from typing import List
from dotenv import load_dotenv
import os

class Settings(BaseSettings):
    APP_NAME: str = "AIS Data"
    APP_STATE: str = Field("prod", env="APP_STATE")
    
    MONGODB_URL: str = Field("mongodb://root:root@localhost:27017", env="MONGODB_URL")
    DB_NAME: str = Field("zenodo", env="DB_NAME")
    MAX_CONNECTIONS_COUNT: int = Field(15, env="MAX_CONNECTIONS_COUNT")
    MIN_CONNECTIONS_COUNT: int = Field(10, env="MIN_CONNECTIONS_COUNT")
    MAX_CURSOR_LENGTH: int = Field(100000000, env="MIN_CONNECTIONS_COUNT")

    DYNAMIC_COLLECTION: str = Field("dynamic_locations", env="DYNAMIC_COLLECTION")
    SSH_CONNECTION: bool = Field(False, env="SSH_CONNECTION")
    SSH_HOST: str = Field("", env="SSH_HOST")
    SSH_USER: str = Field("", env="SSH_USER")
    SSH_PASS: str = Field("", env="SSH_PASS")

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
    
@lru_cache()
def get_settings():
    return Settings()
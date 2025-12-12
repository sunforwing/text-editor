# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # 项目基础信息
    PROJECT_NAME: str = "Logistics System API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # CORS 配置 (允许的前端源)
    # 在生产环境中，应该设置为具体的 Vue 域名，如 ["http://my-vue-app.com"]
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # 数据库配置默认值 (可以通过 .env 文件覆盖)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "123456"     # 请确保这里与你的 MySQL 密码一致
    DB_NAME: str = "logistics_db"

    # 计算属性：生成 SQLAlchemy 连接字符串
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # 配置项：指定读取 .env 文件
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore" # 忽略 .env 中多余的字段
    )

# 实例化配置对象，供其他模块导入使用
settings = Settings()
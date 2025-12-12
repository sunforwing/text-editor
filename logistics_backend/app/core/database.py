# app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 1. 创建数据库引擎
# echo=False 表示不打印每条 SQL 语句到控制台，调试时可改为 True
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # 关键配置：自动处理数据库断连
    pool_recycle=3600,   # 连接池回收时间
    echo=False 
)

# 2. 创建会话工厂
# autocommit=False: 默认不提交，需要手动 db.commit()，保证事务安全性
# autoflush=False: 不自动刷新，避免在未完成逻辑前数据写入数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 创建 ORM 模型基类
# 所有的 Model (如 User, Parcel) 都需要继承这个 Base
Base = declarative_base()

# 4. 依赖项 (Dependency)
# 用于 FastAPI 路由中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # 无论请求处理是否成功，最后一定要关闭数据库连接
        db.close()
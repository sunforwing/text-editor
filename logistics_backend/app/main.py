from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import parcels, transport, delivery, auth
from app.core.database import engine, Base

# 创建数据库表 (如果你不使用 alembic 迁移工具，可以用这行简单的代码自动建表，但你已经有SQL了，这步主要是为了确保ORM映射正常)
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Logistics System API", version="1.0.0")

# 配置 CORS，允许 Vue 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境请改为具体的 Vue 域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(parcels.router)
app.include_router(transport.router)
app.include_router(delivery.router)

@app.get("/")
def root():
    return {"message": "Logistics API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
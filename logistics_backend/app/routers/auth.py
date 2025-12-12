from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.all_models import User
from app.schemas.auth import UserLogin, UserResponse

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"]
)

@router.post("/login", response_model=UserResponse)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    # 1. 根据用户名查找用户
    user = db.query(User).filter(User.username == user_in.username).first()
    
    # 2. 验证用户是否存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    # 3. 验证密码 (注意：实际生产环境应使用哈希验证，这里仅作演示直接比对)
    if user.password_hash != user_in.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
        
    # 4. 返回用户信息
    return user
        
from datetime import datetime, timedelta
import jwt
import bcrypt
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from core.models import User as DBUser
from core.config import  cfg,API_BASE
from sqlalchemy.orm import Session
from core.models import User
import core.db  as db
from passlib.context import CryptContext
import json

DB=db.Db(tag="用户连接")
SECRET_KEY = cfg.get("secret","csol2025")  # 生产环境应使用更安全的密钥
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(cfg.get("token_expire_minutes",30))

class PasswordHasher:
    """自定义密码哈希器，替代passlib的CryptContext"""
    
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """验证密码是否匹配哈希"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def hash(password: str) -> str:
        """生成密码哈希"""
        return bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

# 密码哈希上下文
pwd_context = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{API_BASE}/auth/token",auto_error=False)

# 用户缓存字典
_user_cache = {}
# 登录失败次数记录
_login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5

def get_login_attempts(username: str) -> int:
    """获取用户登录失败次数"""
    return _login_attempts.get(username, 0)

def get_user(username: str) -> Optional[dict]:
    """从数据库获取用户，带缓存功能"""
    # 先检查缓存
    if username in _user_cache:
        return _user_cache[username]
        
    session = DB.get_session()
    try:
        user = session.query(DBUser).filter(DBUser.username == username).first()
        if user:
            # 直接返回SQLAlchemy对象，它已经包含了最新的数据
            _user_cache[username] = user
            return user
        return None
    except Exception as e:
        from core.print import print_error
        print_error(f"获取用户错误: {str(e)}")
        return None
        
def clear_user_cache(username: str):
    """清除指定用户的缓存"""
    if username in _user_cache:
        del _user_cache[username]

from apis.base import error_response
def authenticate_user(username: str, password: str) -> Optional[DBUser]:
    """验证用户凭据"""
    # 检查是否超过最大尝试次数
    if _login_attempts.get(username, 0) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=error_response(
                code=40101,
                message="用户名或密码错误，您的帐号已锁定，请稍后再试"
            )
        )
    
    user = get_user(username)

    if not user or not pwd_context.verify(password, user.password_hash):
        # 增加失败次数
        _login_attempts[username] = _login_attempts.get(username, 0) + 1
        remaining_attempts = MAX_LOGIN_ATTEMPTS - _login_attempts[username]
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=error_response(
                code=40101,
                message=f"用户名或密码错误，您还有{remaining_attempts}次机会"
            )
        )
    
    # 登录成功，清除失败记录
    if username in _login_attempts:
        del _login_attempts[username]
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user(username)
    if user is None:
        raise credentials_exception
        
    return {
        "username": user.username,
        "role": user.role,
        "permissions": user.permissions,
        "original_user": user
    }

def requires_role(role: str):
    """检查用户角色的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or current_user.get('role') != role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def requires_permission(permission: str):
    """检查用户权限的装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user or permission not in current_user.get('permissions', []):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator
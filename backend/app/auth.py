from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import os

# Get secret key from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# Verify password
def verify_password(plain_password, hashed_password):
    # Enhanced debug logging to verify bcrypt is working correctly
    try:
        import bcrypt
        print(f"DEBUG: Using bcrypt version: {bcrypt.__version__}")
        print(f"DEBUG: bcrypt module location: {bcrypt.__file__}")
        
        # Test bcrypt functionality directly
        test_hash = bcrypt.hashpw(b"test", bcrypt.gensalt())
        print(f"DEBUG: bcrypt test hash successful: {test_hash is not None}")
        
        # Check if passlib is using the correct bcrypt
        print(f"DEBUG: CryptContext schemes: {pwd_context.schemes()}")
        print(f"DEBUG: Default scheme: {pwd_context.default_scheme()}")
    except (ImportError, AttributeError) as e:
        print(f"DEBUG: bcrypt import issue: {str(e)}")
        import sys
        print(f"DEBUG: Python path: {sys.path}")
        print(f"DEBUG: Installed packages:")
        import pkg_resources
        for pkg in pkg_resources.working_set:
            print(f"  {pkg.project_name}=={pkg.version}")
    
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        print(f"DEBUG: Password verification result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: Password verification error: {str(e)}")
        raise

# Get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify token
async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    except JWTError:
        raise credentials_exception
    
    # Here you would typically fetch the user from a database
    # For simplicity, we'll just check if it matches the admin username
    if username != os.getenv("ADMIN_USERNAME"):
        raise credentials_exception
    
    return {"username": username, "is_admin": True}

# Verify admin user
async def get_admin_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for admin access"
        )
    return current_user
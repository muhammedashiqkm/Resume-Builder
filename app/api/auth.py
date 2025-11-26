from fastapi import APIRouter, HTTPException, status
from app.core import security
from app.core.config import settings
from app.models.user import UserLogin
from app.models.token import Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """
    Handles user login with a direct password check and returns a JWT.
    """
    if (user_credentials.username == settings.ADMIN_USERNAME and 
        user_credentials.password == settings.ADMIN_PASSWORD):
        
        access_token = security.create_access_token(data={"sub": user_credentials.username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Bad username or password"
    )
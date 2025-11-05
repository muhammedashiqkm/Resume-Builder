from pydantic import BaseModel

class UserLogin(BaseModel):
    """
    Pydantic model for the user login request body.
    """
    username: str
    password: str
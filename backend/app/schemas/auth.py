from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: str | None = None

class PasswordVerifyRequest(BaseModel):
    password: str

class PasswordVerifyResponse(BaseModel):
    valid: bool

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

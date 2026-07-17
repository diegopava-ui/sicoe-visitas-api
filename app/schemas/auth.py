from pydantic import BaseModel


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    usuario_id: int
    username: str
    rol: str
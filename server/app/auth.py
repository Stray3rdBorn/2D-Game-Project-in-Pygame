import os
from dataclasses import dataclass

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: int
    username: str


def read_token(token: str) -> CurrentUser:
    claims = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=["HS256"])
    return CurrentUser(id=int(claims["sub"]), username=claims["username"])


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        return read_token(credentials.credentials)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> CurrentUser | None:
    if credentials is None:
        return None
    try:
        return read_token(credentials.credentials)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
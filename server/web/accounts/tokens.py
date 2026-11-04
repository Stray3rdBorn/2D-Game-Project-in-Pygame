import os
from datetime import datetime, timedelta, timezone

import jwt

TOKEN_LIFETIME = timedelta(days=1)


def make_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "iat": now,
        "exp": now + TOKEN_LIFETIME,
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
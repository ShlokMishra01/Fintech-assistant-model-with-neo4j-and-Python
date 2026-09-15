import base64
import hashlib
import hmac
import json
import time

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from backend.config import (
    APP_PASSWORD,
    APP_USER_ID,
    APP_USERNAME,
    SESSION_COOKIE_SECURE,
    SESSION_SECRET,
    SESSION_TTL_SECONDS,
)
from backend.app.database.neo4j_service import Neo4jService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
SESSION_COOKIE_NAME = "finance_session"


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=256)


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4, max_length=256)
    name: str | None = Field(default=None, max_length=100)
    initial_balance: float = Field(default=0.0, ge=0.0)


def _base64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _sign(payload: str) -> str:
    secret = SESSION_SECRET or "default_secret_key_change_in_production"
    return _base64_encode(
        hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    )


def create_session_token(user_id: str) -> str:
    secret = SESSION_SECRET or "default_secret_key_change_in_production"
    payload = _base64_encode(
        json.dumps({"sub": user_id, "exp": int(time.time()) + SESSION_TTL_SECONDS}, separators=(",", ":")).encode("utf-8")
    )
    return f"{payload}.{_sign(payload)}"


def get_session_user_id(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload, signature = token.split(".", 1)
        if not hmac.compare_digest(signature, _sign(payload)):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if int(data["exp"]) < time.time() or not isinstance(data["sub"], str):
            return None
        return data["sub"]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=SESSION_COOKIE_SECURE,
        samesite="lax",
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, response: Response):
    neo = Neo4jService()
    try:
        user_info = neo.create_user(
            username=payload.username,
            password=payload.password,
            name=payload.name,
            initial_balance=payload.initial_balance
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(err)}")
    finally:
        neo.close()

    user_id = user_info["user_id"]
    token = create_session_token(user_id)
    _set_session_cookie(response, token)
    return {
        "user_id": user_id,
        "username": user_info["username"],
        "name": user_info["name"],
        "token": token
    }


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    # 1. First attempt authentication against Neo4j User nodes
    neo = Neo4jService()
    try:
        user = neo.authenticate_user(payload.username, payload.password)
        if user:
            token = create_session_token(user["user_id"])
            _set_session_cookie(response, token)
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "name": user["name"],
                "token": token
            }
    except Exception:
        pass
    finally:
        neo.close()

    # 2. Fallback to demo environment credentials if configured
    if APP_PASSWORD and SESSION_SECRET:
        valid_username = hmac.compare_digest(payload.username.lower(), APP_USERNAME.lower())
        valid_password = hmac.compare_digest(payload.password, APP_PASSWORD)
        if valid_username and valid_password:
            token = create_session_token(APP_USER_ID)
            _set_session_cookie(response, token)
            return {"user_id": APP_USER_ID, "username": APP_USERNAME, "name": APP_USERNAME, "token": token}

    raise HTTPException(status_code=401, detail="Invalid username or password")


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)


@router.get("/session")
def session(request: Request):
    user_id = get_session_user_id(request.cookies.get(SESSION_COOKIE_NAME))
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Resolve display details
    if user_id == APP_USER_ID:
        return {"user_id": APP_USER_ID, "username": APP_USERNAME, "name": APP_USERNAME}

    neo = Neo4jService()
    try:
        user = neo.get_user_by_id(user_id)
        if user:
            return {
                "user_id": user["user_id"],
                "username": user["username"],
                "name": user["name"]
            }
    except Exception:
        pass
    finally:
        neo.close()

    return {"user_id": user_id, "username": user_id, "name": user_id}

from fastapi import HTTPException, Request
from backend.app.api.auth import SESSION_COOKIE_NAME, get_session_user_id

def get_current_user_id(request: Request) -> str:
    """
    Resolve user identity from signed HTTP-only session cookie,
    Authorization: Bearer <token> header, or X-Session-Token header.
    """
    # 1. Primary: Session cookie
    token = request.cookies.get(SESSION_COOKIE_NAME)

    # 2. Secondary: Bearer authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    # 3. Tertiary: Direct custom header
    if not token:
        token = request.headers.get("X-Session-Token")

    user_id = get_session_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

"""
Connection Gate (connection-level ingress auth)

A lightweight gate on every HTTP request to the MCP endpoint (including
``initialize``/``tools/list``/``ping``) so no fully-anonymous caller can establish
a session. The rule is deliberately simple:

  * **MCP_API_TOKEN set** — static bearer token gate applies to ALL requests
    regardless of auth mode. The ``Authorization`` header must be
    ``Bearer <MCP_API_TOKEN>``. This is checked first, before any other gate.
  * **Server-credential deployments** (dev / local stdio / on-prem — see
    ``settings.uses_server_credentials()``) run entirely on the server's own
    credentials, so the per-user gate is **skipped** — no header is required
    (unless MCP_API_TOKEN is set, see above).
  * **Everywhere else** (production-remote SaaS) a request is allowed iff a
    credential is present in a request **header**: the ``Authorization`` header
    (type 1) or any configured API-key header (type 4, ``get_apikey_header_names()``).
    Otherwise the connection is rejected with 401.

This is the **channel** layer (is the caller allowed to connect?), distinct from
the per-call **user** resolver in ``AuthService`` (which OP user?). The gate looks
only at headers; the body context vars ``op_auth_header``/``op_auth_ticket`` (types
2 & 4) are not inspected here — in the Orchestrate flow the API-key header secures
the connection while the higher-priority ``op_auth_ticket`` drives tool calls.

No credential value is ever logged.
"""

import logging
import secrets

from fastapi import HTTPException, Request

from src.app.config.settings import settings

logger = logging.getLogger(__name__)


def _check_static_token(request: Request) -> bool:
    """Validate the static MCP_API_TOKEN bearer if one is configured.

    Returns True if the token matches, False if the header is absent or wrong.
    Uses a constant-time comparison to prevent timing attacks.
    """
    expected = settings.MCP_API_TOKEN.strip()
    if not expected:
        return True  # No static token configured — gate not active.

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return False

    provided = auth_header[len("bearer "):].strip()
    return secrets.compare_digest(provided, expected)


def _has_user_header(request: Request) -> bool:
    """Whether a user credential header is present (type 1 Authorization or type 4 API key)."""
    if request.headers.get("Authorization"):
        return True
    for header_name in settings.get_apikey_header_names():
        if request.headers.get(header_name):
            return True
    return False


async def require_channel_auth(request: Request) -> None:
    """FastAPI dependency: require a header credential to connect.

    Static token gate (MCP_API_TOKEN) is checked first for all deployments.
    For server-credential deployments the per-user gate is then skipped.

    Raises:
        HTTPException(401): If any active gate rejects the request.
    """
    # --- Static token gate (all modes) ---
    if settings.MCP_API_TOKEN.strip():
        if not _check_static_token(request):
            logger.warning("Rejecting connection: invalid or missing MCP_API_TOKEN")
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Token matched — skip the per-user header gate entirely.
        return

    # --- Per-user header gate (user-auth mode only) ---
    if settings.uses_server_credentials():
        # dev / local / on-prem: server credentials run everything, no gate.
        return

    if _has_user_header(request):
        return

    logger.warning("Rejecting connection: no Authorization or API-key header present")
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )

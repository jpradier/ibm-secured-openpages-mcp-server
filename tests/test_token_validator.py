"""
Tests for PassthroughTokenValidator.

Validates:
- Valid token (with/without Bearer prefix)
- Expired token raises TokenValidationError
- Malformed JWT (wrong segment count, bad base64, bad JSON)
- Missing exp claim
- Cache hit — same token, still valid
- Cache hit — same token, now expired
- New token replaces cache
"""

import base64
import json
import time

import pytest

from src.app.auth.token_validator import PassthroughTokenValidator, TokenValidationError


def _make_jwt(payload: dict, header: dict = None) -> str:
    """Build a minimal unsigned JWT (header.payload.signature)."""
    header = header or {"alg": "none", "typ": "JWT"}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{h}.{p}.fakesig"


def _make_valid_token(exp_offset: int = 3600) -> str:
    """Return a JWT that expires exp_offset seconds from now."""
    return _make_jwt({"sub": "user1", "exp": time.time() + exp_offset})


def _make_expired_token() -> str:
    """Return a JWT that expired 1 hour ago."""
    return _make_jwt({"sub": "user1", "exp": time.time() - 3600})


@pytest.mark.asyncio
class TestValidToken:
    """Valid tokens should pass without error."""

    async def test_valid_token_no_prefix(self):
        validator = PassthroughTokenValidator()
        token = _make_valid_token()
        await validator.validate(token)  # should not raise

    async def test_valid_token_with_bearer_prefix(self):
        validator = PassthroughTokenValidator()
        token = "Bearer " + _make_valid_token()
        await validator.validate(token)

    async def test_valid_token_with_lowercase_bearer_prefix(self):
        validator = PassthroughTokenValidator()
        token = "bearer " + _make_valid_token()
        await validator.validate(token)


@pytest.mark.asyncio
class TestBasicAuth:
    """Basic auth credentials must bypass JWT validation entirely."""

    async def test_basic_auth_passes_without_error(self):
        validator = PassthroughTokenValidator()
        # Should not raise — Basic credentials are not JWTs
        await validator.validate("Basic T3BlblBhZ2VzQWRtaW5pc3RyYXRvcjpPcGVuUGFnZXNBZG1pbmlzdHJhdG9y")

    async def test_basic_auth_lowercase_passes_without_error(self):
        validator = PassthroughTokenValidator()
        await validator.validate("basic dXNlcjpwYXNz")

    async def test_basic_auth_does_not_populate_cache(self):
        validator = PassthroughTokenValidator()
        await validator.validate("Basic dXNlcjpwYXNz")
        # Cache must stay empty — Basic credentials are not JWTs
        assert validator._cached_token is None


@pytest.mark.asyncio
class TestExpiredToken:
    """Expired tokens should raise TokenValidationError."""

    async def test_expired_token(self):
        validator = PassthroughTokenValidator()
        token = _make_expired_token()
        with pytest.raises(TokenValidationError, match="expired"):
            await validator.validate(token)


@pytest.mark.asyncio
class TestMalformedToken:
    """Malformed tokens should raise TokenValidationError."""

    async def test_wrong_segment_count_one(self):
        validator = PassthroughTokenValidator()
        with pytest.raises(TokenValidationError, match="expected 3 segments"):
            await validator.validate("not-a-jwt")

    async def test_wrong_segment_count_two(self):
        validator = PassthroughTokenValidator()
        with pytest.raises(TokenValidationError, match="expected 3 segments"):
            await validator.validate("part1.part2")

    async def test_bad_base64_payload(self):
        validator = PassthroughTokenValidator()
        with pytest.raises(TokenValidationError, match="invalid base64|not valid JSON"):
            await validator.validate("header.!!!invalid!!!.sig")

    async def test_bad_json_payload(self):
        validator = PassthroughTokenValidator()
        # Valid base64 but not valid JSON
        payload_b64 = base64.urlsafe_b64encode(b"not json").rstrip(b"=").decode()
        with pytest.raises(TokenValidationError, match="not valid JSON"):
            await validator.validate(f"header.{payload_b64}.sig")

    async def test_missing_exp_claim(self):
        validator = PassthroughTokenValidator()
        token = _make_jwt({"sub": "user1"})  # no exp
        with pytest.raises(TokenValidationError, match="missing required 'exp'"):
            await validator.validate(token)

    async def test_invalid_exp_type(self):
        validator = PassthroughTokenValidator()
        token = _make_jwt({"sub": "user1", "exp": "not-a-number"})
        with pytest.raises(TokenValidationError, match="not a valid number"):
            await validator.validate(token)


@pytest.mark.asyncio
class TestCache:
    """Cache behavior tests."""

    async def test_cache_hit_same_token_still_valid(self):
        """Second call with same token should use cache and pass."""
        validator = PassthroughTokenValidator()
        token = _make_valid_token()
        await validator.validate(token)
        # Call again — should hit cache
        await validator.validate(token)
        # Verify cache state
        assert validator._cached_token is not None

    async def test_cache_hit_same_token_now_expired(self):
        """If cached token's exp is now in the past, raise error."""
        validator = PassthroughTokenValidator()
        # Token that expires in 1 second
        token = _make_jwt({"sub": "user1", "exp": time.time() + 1})
        await validator.validate(token)

        # Manually set cached exp to the past to simulate expiry
        validator._cached_exp = time.time() - 1
        with pytest.raises(TokenValidationError, match="expired"):
            await validator.validate(token)
        # Cache should be cleared
        assert validator._cached_token is None

    async def test_new_token_replaces_cache(self):
        """A different token should replace the cached one."""
        validator = PassthroughTokenValidator()
        token1 = _make_valid_token(exp_offset=3600)
        token2 = _make_valid_token(exp_offset=7200)

        await validator.validate(token1)
        stripped1 = validator._cached_token

        await validator.validate(token2)
        stripped2 = validator._cached_token

        assert stripped1 != stripped2

    async def test_bearer_prefix_stripped_for_cache(self):
        """Bearer prefix should be stripped before caching."""
        validator = PassthroughTokenValidator()
        raw_token = _make_valid_token()
        await validator.validate("Bearer " + raw_token)
        assert validator._cached_token == raw_token

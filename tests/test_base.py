from unittest.mock import MagicMock, patch

import pytest

from aegis import ForbiddenException
from aegis.authenticators.base import BaseAuthenticator


async def test_check_permissions_returns_uses_any_match_as_default():
    user_permissions = ("super_user",)

    required_permissions = ("super_user",)
    with patch("aegis.authenticators.base.match_any") as match_any:
        has_permissions = await BaseAuthenticator.check_permissions(
            user_permissions, required_permissions
        )

        assert has_permissions
        match_any.assert_called_once_with(
            required=required_permissions, provided=user_permissions
        )


async def test_check_permissions_returns_with_calls_any_match_algorithm():
    user_permissions = ("regular_user",)

    required_permissions = ("super_user", "regular_user")
    with patch("aegis.authenticators.base.match_any") as match_any:
        has_permissions = await BaseAuthenticator.check_permissions(
            user_permissions, required_permissions, algorithm="any"
        )

        assert has_permissions
        match_any.assert_called_once_with(
            required=required_permissions, provided=user_permissions
        )


async def test_check_permissions_returns_calls_all_match_algorithm():
    user_permissions = ("regular_user",)

    required_permissions = ("super_user", "regular_user")

    with patch("aegis.authenticators.base.match_all") as match_all:
        match_all.return_value = True
        has_permissions = await BaseAuthenticator.check_permissions(
            user_permissions, required_permissions, algorithm="all"
        )

        assert has_permissions
        match_all.assert_called_once_with(
            required=required_permissions, provided=user_permissions
        )


async def test_check_permissions_returns_calls_exact_match_algorithm():
    user_permissions = ("regular_user",)

    required_permissions = ("super_user", "regular_user")

    with patch("aegis.authenticators.base.match_exact") as match_exact:
        match_exact.return_value = True
        has_permissions = await BaseAuthenticator.check_permissions(
            user_permissions, required_permissions, algorithm="exact"
        )

        assert has_permissions
        match_exact.assert_called_once_with(
            required=required_permissions, provided=user_permissions
        )


async def test_check_permissions_returns_calls_custom_algorithm():
    user_permissions = ("regular_user",)

    required_permissions = ("super_user", "regular_user")

    custom_mock = MagicMock(return_value=True)

    def custom_algorithm(*args, **kwargs):
        return custom_mock(*args, **kwargs)

    has_permissions = await BaseAuthenticator.check_permissions(
        user_permissions, required_permissions, algorithm=custom_algorithm
    )

    assert has_permissions
    custom_mock.assert_called_once_with(required_permissions, user_permissions)


async def test_check_permissions_handles_invalid_algorithm():

    user_permissions = ("regular_user",)

    required_permissions = ("super_user", "regular_user")

    invalid_algorithm = object()

    with pytest.raises(TypeError) as te:
        # noinspection PyTypeChecker
        await BaseAuthenticator.check_permissions(
            user_permissions, required_permissions, algorithm=invalid_algorithm
        )

    assert str(te.value) == (
        "Invalid algorithm type. Options 'all', 'any', 'exact', callable"
    )


async def test_get_scopes_returns_user_permissions_with_default_key():
    class TestBaseAuth(BaseAuthenticator):
        async def decode(self, token: str) -> dict:
            pass

        async def get_user(self, credentials) -> dict:
            pass

        async def authenticate(self, request):
            pass

    auth = TestBaseAuth()

    mock_request = MagicMock()
    mock_request.user = {"permissions": ("test",)}

    scopes = await auth.get_permissions(mock_request)

    assert scopes == ("test",)


async def test_get_scopes_returns_user_permissions_with_altered_key():
    class TestBaseAuth(BaseAuthenticator):
        permission_key = "test_key"

        async def decode(self, token: str) -> dict:
            pass

        async def get_user(self, credentials) -> dict:
            pass

        async def authenticate(self, request):
            pass

    auth = TestBaseAuth()

    mock_request = MagicMock()
    mock_request.user = MagicMock()

    await auth.get_permissions(mock_request)

    mock_request.user.get.assert_called_with("test_key")


async def test_get_scopes_raises_forbidden_if_user_is_not_available():
    class TestBaseAuth(BaseAuthenticator):
        async def decode(self, token: str) -> dict:
            pass

        async def get_user(self, credentials) -> dict:
            pass

        async def authenticate(self, request):
            pass

    auth = TestBaseAuth()

    with pytest.raises(ForbiddenException):
        mock_request = object()
        await auth.get_permissions(mock_request)

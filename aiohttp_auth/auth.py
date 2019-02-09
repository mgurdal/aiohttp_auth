import jwt
from datetime import datetime, timedelta

from typing import Callable, Union
from aiohttp import web
from aiohttp.web import json_response


async def generate_jwt(request: web.Request, payload: dict) -> str:
    delta_seconds = request.app['aiohttp_auth'].duration
    jwt_data = {
        **payload,
        'exp': datetime.utcnow() + timedelta(seconds=delta_seconds)
    }

    jwt_token = jwt.encode(
        jwt_data,
        request.app['aiohttp_auth'].jwt_secret,
        request.app['aiohttp_auth'].jwt_algorithm
    )
    token = jwt_token.decode('utf-8')

    return token


def check_permissions(request: web.Request, scopes: Union[set, tuple]) -> bool:
    # if a user injected into request by the auth_middleware
    user = getattr(request, 'user', None)
    has_permission = False
    if user:
        # if a non-anonymous user tries to reach to
        # a scoped endpoint
        user_is_anonymous = user['scopes'] == ('anonymous_user',)
        if not user_is_anonymous:
            user_scopes = set(request.user['scopes'])
            required_scopes = set(scopes)
            if user_scopes.intersection(required_scopes):
                has_permission = True

    return has_permission


def scopes(*required_scopes: Union[set, tuple]) -> web.json_response:
    assert required_scopes, 'Cannot be used without any scope!'

    def request_handler(view: Callable) -> Callable:
        async def wrapper(request: web.Request):
            if not isinstance(request, web.Request):
                raise TypeError(F"Invalid Type '{type(request)}'")

            has_permission = check_permissions(request, required_scopes)

            if not has_permission:
                return json_response(
                    {'message': 'Forbidden', "errors": []},
                    status=403
                )
            else:
                return await view(request)

        return wrapper
    return request_handler


def middleware(user_injector: Callable) -> web.middleware:
    @web.middleware
    async def wrapper(request: web.Request, handler: Callable):
        if 'aiohttp_auth' not in request.app:
            raise AttributeError('Please initialize aiohttp_auth first.')

        jwt_token = request.headers.get('authorization')
        if jwt_token:
            try:
                jwt_token = jwt_token.replace('Bearer ', '')
                jwt.decode(
                    jwt_token,
                    request.app['aiohttp_auth'].jwt_secret,
                    algorithms=[request.app['aiohttp_auth'].jwt_algorithm]
                )
                user = await user_injector(request)
                request.user = user
                return await handler(request)
            except jwt.DecodeError:
                return json_response(
                    {'message': 'Invalid Token', "errors": []},
                    status=401
                )
            except jwt.ExpiredSignatureError:
                return json_response(
                    {'message': 'Token Has Expired', "errors": []},
                    status=401
                )
        else:
            return json_response(
                {
                    "message": "Please enter your API key.",
                    "errors": []
                }, status=401)
    return wrapper


class JWTAuth:
    def __init__(self, jwt_secret: str, duration: int, jwt_algorithm: str):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.duration = duration


def setup(app, jwt_secret, duration=259200, jwt_algorithm='HS256'):
    app['aiohttp_auth'] = JWTAuth(jwt_secret, duration, jwt_algorithm)
    return app

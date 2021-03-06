from uuid import uuid4

from aiohttp import web
from aegis import JWTAuth, login_required


def find_user_with_name(database: dict, name: str) -> dict:
    # search for user with name
    user_query = [
        {**user, "id": id} for id, user in database.items() if user["name"] == name
    ]
    if user_query:
        return user_query[0]


class JWTAuthenticator(JWTAuth):
    jwt_secret: str = "<secret>"
    refresh_token: bool = True  # enables refresh token feature
    duration: int = 3  # short expiration date

    async def authenticate(self, request: web.Request) -> dict:
        payload = await request.json()
        user = find_user_with_name(request.app["db"], payload["name"])
        return user

    async def validate_refresh_token(self, request: web.Request) -> bool:
        """
        You should handle the refresh token provided by user using the
        /auth/refresh route. This route is login required by default.
        :return: Whether the refresh token is valid or not.
        """
        payload = await request.json()

        provided_token = payload["refresh_token"]
        user = request.user

        # Get user's refresh token from database
        user = find_user_with_name(request.app["db"], user["name"])
        expected_token = user["refresh_token"]

        if provided_token != expected_token:
            return False
        return True

    async def get_refresh_token(self, request) -> str:
        # Generate refresh token for user
        refresh_token = str(uuid4()).replace("-", "")

        user = request.user
        # Hold user's refresh token in somewhere persistent
        request.app["db"][user["id"]]["refresh_token"] = refresh_token

        user["refresh_token"] = refresh_token

        return refresh_token


@login_required
async def protected(request):
    return web.json_response({"hello": "user"})


def create_app():
    app = web.Application()

    database = {5: {"name": "david", "refresh_token": None}}
    app["db"] = database

    app.router.add_get("/protected", protected)

    JWTAuthenticator.setup(app)
    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app)

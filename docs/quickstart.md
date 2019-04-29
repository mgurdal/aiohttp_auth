Quickstart
==========

In this page, we will explore how we can access and authorize a user in the 
database using aegis.

Installation
------------

```bash
pip3 install aegis
```

Simple example
--------------

The library API is pretty minimalistic: create an authenticator,
implement authentication logic, decorate routes.

Create an authenticator:
```python
from aegis.authenticators.jwt import JWTAuth

class JWTAuthenticator(JWTAuth):
    jwt_secret = "<secret>"

    async def authenticate(self, request: web.Request) -> dict:
        ...
```

Implement the authentication logic:
```python
    async def authenticate(self, request: web.Request) -> dict:
        # You can get the request payload of the /auth route
        payload = await request.json()

        # Assuming the name parameter send in the request payload
        searched_name = payload["name"]

        # fetch the user from your storage
        db = request.app["db"]
        user = db.get(searched_name, None)

        # return the JSON serializable user
        return user
```

Decorate route:
```python
    @auth.login_required
    async def protected(request):
        return web.json_response({'hello': 'user'})
```

Let's collect it altogether into very small but still functional
example:
```python
    from aiohttp import web
    from aegis import auth
    from aegis.authenticators.jwt import JWTAuth


    class JWTAuthenticator(JWTAuth):
        jwt_secret = "test"

        async def authenticate(self, request: web.Request) -> dict:
            # You can get the request payload of the /auth route
            payload = await request.json()

            # Assuming the name parameter send in the request payload
            searched_name = payload["name"]

            # fetch the user from your storage
            db = request.app["db"]
            user = db.get(searched_name, None)

            # return the JSON serializable user
            return user

    @auth.login_required
    async def protected(request):
        return web.json_response({'hello': 'user'})


    app = web.Application()

    DATABASE = {
        'david': {'id': 5}
    }
    app["db"] = DATABASE

    app.router.add_get('/', protected)

    JWTAuthenticator.setup(app)

    web.run_app(app)
```

We can now navigate to http://0.0.0.0:8080 to check whether its
protected or not.

In order to get to the route. We first need to get an access token. We
can do it by sending the required credentials to the pre-defined /auth/
route.

Authentication request:
```bash
curl -X POST http://0.0.0.0:8080/auth -d '{
    "name": "david"
}'
```

If everything goes OK we will get the access\_token as response.
```json
{
    "access_token": "eyJ..."
}
```

Otherwise we will get one of the pre-defined UNAUTHORIZED response. :
```json
{
    "type": "https://mgurdal.github.io/aiohttp_auth/docs.html#unauthorized",
    "title": "Authentication failed.",
    "detail": "The credentials you supplied were not correct.",
    "instance": "http://0.0.0.0:8080/auth",
    "status": "401"
}
```
We can use the access token to reach to the protected route. :
```bash
curl http://0.0.0.0:8080/ -H 'Authorization: Bearer eyJ...'
```
```json
{"hello": "user"}
```
That's pretty much it.

Future reading
--------------

For more info about library design and principles read aegis-intro.

API reference is here: aegis-api.
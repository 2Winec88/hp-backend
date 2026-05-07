from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = self._get_token(scope)
        scope['user'] = await self._get_user(token) if token else AnonymousUser()
        return await super().__call__(scope, receive, send)

    def _get_token(self, scope):
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            return token

        for header_name, header_value in scope.get('headers', []):
            if header_name == b'authorization':
                auth_header = header_value.decode()
                if auth_header.startswith('Bearer '):
                    return auth_header.removeprefix('Bearer ').strip()

        return None

    @database_sync_to_async
    def _get_user(self, token):
        jwt_authentication = JWTAuthentication()

        try:
            validated_token = jwt_authentication.get_validated_token(token)
            return jwt_authentication.get_user(validated_token)
        except (InvalidToken, TokenError):
            return AnonymousUser()

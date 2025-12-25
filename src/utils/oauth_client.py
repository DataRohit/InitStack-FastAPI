from authlib.integrations.starlette_client import OAuth

from config.settings import settings

oauth: OAuth = OAuth()

oauth.register(
    name="google",
    client_id=settings.oauth_google_client_id,
    client_secret=settings.oauth_google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)

oauth.register(
    name="github",
    client_id=settings.oauth_github_client_id,
    client_secret=settings.oauth_github_client_secret,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    access_token_url="https://github.com/login/oauth/access_token",  # noqa: S106
    access_token_params=None,
    api_base_url="https://api.github.com/",
    client_kwargs={
        "scope": "user:email",
    },
)

__all__: list[str] = ["oauth"]

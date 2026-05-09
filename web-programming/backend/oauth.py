"""OAuth2 provider registrations (Google, GitHub, Discord) via authlib."""

from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from backend.config import (
    DROPBOX_CLIENT_ID,
    DROPBOX_CLIENT_SECRET,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)

oauth = OAuth()

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

if DROPBOX_CLIENT_ID and DROPBOX_CLIENT_SECRET:
    oauth.register(
        name="dropbox",
        client_id=DROPBOX_CLIENT_ID,
        client_secret=DROPBOX_CLIENT_SECRET,
        access_token_url="https://api.dropboxapi.com/oauth2/token",
        authorize_url="https://www.dropbox.com/oauth2/authorize",
        api_base_url="https://api.dropboxapi.com/2/",
        client_kwargs={"scope": "account_info.read"},
    )

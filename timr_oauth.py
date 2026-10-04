"""
OAuth2 client for the Timr.com authorization server

Handles the authorization code flow with PKCE used for the user login, token
refresh and revocation, and the client credentials flow used by developer tools
and integration tests.

Copyright (c) 2025 Ohrner IT GmbH
Licensed under the MIT License
"""

import base64
import hashlib
import logging
import secrets
import time
from urllib.parse import urlencode

import requests

from config import OAUTH_ISSUER, REQUEST_TIMEOUT_SECONDS
from timr_api import TimrApiError

logger = logging.getLogger(__name__)

# OpenID Connect Discovery: location of the provider metadata relative to the issuer
DISCOVERY_PATH = "/.well-known/openid-configuration"

# Scopes defined by Timr.com for the respective grant types
USER_SCOPES = "openid offline_access"
CLIENT_CREDENTIALS_SCOPES = "openid timrclient"

# Access tokens are refreshed this many seconds before they expire
TOKEN_REFRESH_MARGIN_SECONDS = 60


def create_pkce_pair():
    """
    Create a PKCE code verifier and its S256 code challenge (RFC 7636).

    Returns:
        tuple: (code_verifier, code_challenge)
    """
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def token_expires_soon(expires_at):
    """
    Check whether an access token has to be refreshed before it is used.

    Args:
        expires_at (int or None): Expiry as Unix timestamp, None if unknown

    Returns:
        bool: True if the token expires within the refresh margin
    """
    if expires_at is None:
        return False
    return time.time() + TOKEN_REFRESH_MARGIN_SECONDS >= expires_at


def token_is_expired(expires_at):
    """
    Check whether an access token can no longer be used.

    Args:
        expires_at (int or None): Expiry as Unix timestamp, None if unknown

    Returns:
        bool: True if the token has expired
    """
    if expires_at is None:
        return False
    return time.time() >= expires_at


class TimrOAuthClient:
    """
    Client for the Timr.com authorization server.

    The endpoints are read from the OpenID Provider metadata of the issuer on
    first use and kept for the lifetime of the client.
    """

    def __init__(self, client_id, client_secret, redirect_uri=None, issuer=OAUTH_ISSUER):
        """
        Initialize the OAuth client.

        Args:
            client_id (str): OAuth client ID configured in Timr.com
            client_secret (str): OAuth client secret
            redirect_uri (str, optional): Redirect URI for the authorization code flow
            issuer (str, optional): Issuer of the authorization server
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.issuer = issuer
        self.session = requests.Session()
        self._provider_metadata = None

    def authorization_url(self, state, code_challenge):
        """
        Build the URL the user's browser is sent to for logging in at Timr.com.

        Args:
            state (str): Random value protecting the callback against forgery
            code_challenge (str): PKCE S256 code challenge

        Returns:
            str: Authorization endpoint URL including all parameters
        """
        return self._endpoint("authorization_endpoint") + "?" + urlencode({
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": USER_SCOPES,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        })

    def exchange_code(self, code, code_verifier):
        """
        Exchange an authorization code for access and refresh token.

        Returns:
            dict: Tokens, see _request_tokens
        """
        return self._request_tokens({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier,
        })

    def refresh_tokens(self, refresh_token):
        """
        Obtain a new access token using a refresh token.

        The authorization server may rotate the refresh token; if it does not
        return a new one, the given refresh token stays valid.

        Returns:
            dict: Tokens, see _request_tokens
        """
        if not refresh_token:
            raise TimrApiError("Your Timr.com session has expired. Please log in again.")
        tokens = self._request_tokens({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        })
        if not tokens["refresh_token"]:
            tokens["refresh_token"] = refresh_token
        return tokens

    def fetch_client_credentials_tokens(self):
        """
        Obtain an access token for the client itself (no user login involved).

        Returns:
            dict: Tokens, see _request_tokens
        """
        return self._request_tokens({
            "grant_type": "client_credentials",
            "scope": CLIENT_CREDENTIALS_SCOPES,
        })

    def fetch_user_id(self, access_token):
        """
        Determine the Timr.com user ID of an access token via the userinfo endpoint.

        Returns:
            str: User ID (OpenID Connect subject)
        """
        response = self._send("GET", self._endpoint("userinfo_endpoint"),
                              headers={"Authorization": f"Bearer {access_token}"})
        return response.json()["sub"]

    def revoke_token(self, token, token_type_hint="refresh_token"):
        """Revoke a token at the authorization server (RFC 7009)."""
        self._send("POST", self._endpoint("revocation_endpoint"), data=self._with_client_authentication({
            "token": token,
            "token_type_hint": token_type_hint,
        }))

    def _request_tokens(self, grant_data):
        """
        Send a token request and normalize the response.

        Returns:
            dict: access_token, refresh_token (None if not issued) and expires_at
                  (Unix timestamp, None if the server did not state a lifetime)
        """
        payload = self._send("POST", self._endpoint("token_endpoint"),
                             data=self._with_client_authentication(grant_data)).json()
        expires_in = payload.get("expires_in")
        return {
            "access_token": payload["access_token"],
            "refresh_token": payload.get("refresh_token"),
            "expires_at": int(time.time()) + expires_in if expires_in is not None else None,
        }

    def _endpoint(self, name):
        """
        Get an endpoint URL from the provider metadata, loading it on first use.

        Args:
            name (str): Metadata field, e.g. "token_endpoint"

        Raises:
            TimrApiError: If the metadata cannot be loaded, belongs to another
                          issuer (OpenID Connect Discovery 1.0, section 4.3) or
                          lacks the endpoint
        """
        if self._provider_metadata is None:
            metadata = self._send("GET", self.issuer + DISCOVERY_PATH).json()
            if metadata.get("issuer") != self.issuer:
                logger.error(f"Provider metadata of {self.issuer} names issuer {metadata.get('issuer')!r}")
                raise TimrApiError("Timr.com login service is misconfigured. Please try again later.")
            self._provider_metadata = metadata

        if name not in self._provider_metadata:
            logger.error(f"Provider metadata of {self.issuer} lacks {name}")
            raise TimrApiError("Timr.com login service is misconfigured. Please try again later.")
        return self._provider_metadata[name]

    def _with_client_authentication(self, data):
        return {**data, "client_id": self.client_id, "client_secret": self.client_secret}

    def _send(self, method, url, **kwargs):
        """
        Send a request to the authorization server.

        Raises:
            TimrApiError: If the request fails; the technical message contains the
                          OAuth error code and description but never any credentials
        """
        try:
            if method == "POST":
                response = self.session.post(url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
            else:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"OAuth request {method} {url} failed: {e}")
            raise TimrApiError("Timr.com login service is not reachable. Please try again later.") from e

        if not response.ok:
            try:
                error_body = response.json()
            except ValueError:
                error_body = {}
            technical_message = (f"OAuth request {method} {url} failed with status "
                                 f"{response.status_code}: {error_body.get('error', '')} "
                                 f"{error_body.get('error_description', '')}").strip()
            logger.warning(technical_message)
            error = TimrApiError("Timr.com rejected the request. Please try again.",
                                 response.status_code, error_body)
            error.technical_message = technical_message
            raise error

        return response

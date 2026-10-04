"""
Helpers for simulating the HTTP boundary with real requests.Response objects.
"""

import json

import requests


def make_json_response(status_code, body, content_type="application/json"):
    """Build a real requests.Response carrying a JSON body."""
    response = requests.Response()
    response.status_code = status_code
    response._content = json.dumps(body).encode("utf-8")
    response.headers["Content-Type"] = content_type
    return response

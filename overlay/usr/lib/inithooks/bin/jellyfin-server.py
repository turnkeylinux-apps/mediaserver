#!/usr/bin/python3
"""Set the Jellyfin administrator password during first boot."""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:8096"
BOOTSTRAP_PASSWORD_FILE = "/etc/jellyfin/turnkey-bootstrap-password"
AUTHORIZATION = (
    'MediaBrowser Client="TurnKey Linux", Device="First boot", '
    'DeviceId="turnkey-firstboot", Version="19"'
)


def api_request(path, payload=None, token=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "X-Emby-Authorization": AUTHORIZATION,
    }
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["X-Emby-Token"] = token

    request = urllib.request.Request(
        BASE_URL + path,
        data=data,
        headers=headers,
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body) if body else None


def prompt_password():
    try:
        from libinithooks.dialog_wrapper import Dialog
    except ImportError as error:
        raise RuntimeError("a password must be supplied with --pass") from error

    dialog = Dialog("TurnKey Linux - First boot configuration")
    return dialog.get_password(
        "Jellyfin Password",
        "Enter a new password for the Jellyfin administrator account.",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pass", dest="password")
    args = parser.parse_args()
    password = args.password if args.password is not None else prompt_password()
    if not password:
        raise RuntimeError("the Jellyfin administrator password cannot be empty")

    try:
        with open(BOOTSTRAP_PASSWORD_FILE, encoding="utf-8") as password_file:
            bootstrap_password = password_file.read().rstrip("\n")
    except FileNotFoundError as error:
        raise RuntimeError("the Jellyfin bootstrap credential is missing") from error

    try:
        authentication = api_request(
            "/Users/AuthenticateByName",
            {"Username": "jellyfin", "Pw": bootstrap_password},
        )
        token = authentication.get("AccessToken") if authentication else None
        if not isinstance(token, str) or not token:
            raise RuntimeError("Jellyfin did not return an access token")

        api_request(
            "/Users/Password",
            {
                "CurrentPw": bootstrap_password,
                "NewPw": password,
                "ResetPassword": False,
            },
            token,
        )
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace").strip()
        message = f"Jellyfin returned HTTP {error.code}"
        if detail:
            message += f": {detail}"
        raise RuntimeError(message) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"cannot reach Jellyfin: {error.reason}") from error

    os.unlink(BOOTSTRAP_PASSWORD_FILE)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

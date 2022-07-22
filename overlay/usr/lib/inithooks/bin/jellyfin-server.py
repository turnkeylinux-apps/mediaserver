#!/usr/bin/python3
# Copyright (c) 2015 Jonathan Struebel <jonathan.struebel@gmail.com>
# Modified for Jellyfin 2019 TurnKey GNU/Linux <jeremy@turnkeylinux.org>
"""Configure Jellyfin Media Server

Arguments:
    none

Options:
    -p --pass=    if not provided, will ask interactively
"""

import sys
import getopt
import signal
import hashlib
import secrets
import base64
import sqlite3

def fatal(s):
    print("Error:", s, file=sys.stderr)
    sys.exit(1)

def usage(s=None):
    if s:
        print("Error:", s, file=sys.stderr)
    print("Syntax: %s [options]" % sys.argv[0], file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)

def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hp:", ['help', 'pass='])
    except getopt.GetoptError as e:
        usage(e)

    password = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-p', '--pass'):
            password = val

    if not password:
        from libinithooks.dialog_wrapper import Dialog
        d = Dialog('TurnKey GNU/Linux - First boot configuration')
        password = d.get_password(
            "Jellyfin User Password",
            "Please enter new password for the Jellyfin Server jellyfin account.")

    # taken from https://github.com/jellyfin/jellyfin/blob/master/MediaBrowser.Common/Cryptography/Constants.cs
    salt = secrets.token_bytes(64)
    iterations = 1000
    dklen = 32
    # dklen taken fromm the r.GetBytes(32) line at https://github.com/jellyfin/jellyfin/blob/master/Emby.Server.Implementations/Cryptography/CryptographyProvider.cs
    hashed_pw = hashlib.pbkdf2_hmac("sha1", password.encode(), salt, iterations, dklen)

    formatted_pw = '$PBKDF2$iterations={iterations}${salt}${hashed_pw}'.format(
            iterations=iterations,
            hashed_pw=base64.b16encode(hashed_pw).decode(),
            salt=base64.b16encode(salt).decode())

    conn = sqlite3.connect('/var/lib/jellyfin/data/jellyfin.db')
    c = conn.cursor()
    c.execute('UPDATE Users SET Password=? WHERE Username=?;', (formatted_pw, "jellyfin"))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()


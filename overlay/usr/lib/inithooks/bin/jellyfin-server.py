#!/usr/bin/python
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
import subprocess
from subprocess import PIPE
import signal
import JellyfinTools
from JellyfinTools import UserClient
import json

def fatal(s):
    print >> sys.stderr, "Error:", s
    sys.exit(1)

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

def main():
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hp:", ['help', 'pass='])
    except getopt.GetoptError, e:
        usage(e)

    jellyfin = UserClient()

    password = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-p', '--pass'):
            password = val

    if not password:
        from dialog_wrapper import Dialog
        d = Dialog('TurnKey GNU/Linux - First boot configuration')
        password = d.get_password(
            "Jellyfin User Password",
            "Please enter new password for the Jellyfin Server %s account." % jellyfin.getUsername())

    pwfile = "/etc/jellyfinpass"
    oldpw = None
    try:
        f = open(pwfile,'r')
    except:
        oldpw = ""
    else:
        oldpw = f.readline().rstrip('\r\n')
        f.close()

    server = jellyfin.getServer()
    url = "%s/web/login.html" % server
    status = jellyfin.doUtils.downloadUrl(url, json=False, authenticate=False)

    if (status == 302 or status == 'Redirect'):
        # Perform initial Jellyfin setup
        settings = "/etc/jellyfininitsetup"
        try:
            f = open(settings,'r')
        except:
            return

        for line in f:
            fields = line.split('|')
            if '#' in fields[0]:
                continue

            jsonEnc = False
            if (fields[2] == "json"):
                jsonEnc = True
            fields[1] = fields[1].replace("{server}", server, 1)
            fields[1] = fields[1].replace("{user}", jellyfin.getUsername(), 1)
            if len(fields) > 3:
                fields[3] = fields[3].replace("{user}", jellyfin.getUsername(), 1)
                jellyfin.doUtils.downloadUrl(fields[1], postBody=fields[3], type=fields[0], json=jsonEnc, authenticate=False)
            else:
                jellyfin.doUtils.downloadUrl(fields[1], type=fields[0], json=jsonEnc, authenticate=False)

        f.close()

    jellyfin.currPass = oldpw
    jellyfin.authenticate()

    # Perform remaining Jellyfin setup
    settings = "/etc/jellyfinsetup"
    try:
        f = open(settings,'r')
    except:
        return

    for line in f:
        fields = line.split('|')
        if '#' in fields[0]:
            continue

        jsonEnc = False
        if (fields[2] == "json"):
            jsonEnc = True
        fields[1] = fields[1].replace("{server}", server, 1)
        fields[1] = fields[1].replace("{user}", jellyfin.getUsername(), 1)
        if len(fields) > 3:
            fields[3] = fields[3].replace("{user}", jellyfin.getUsername(), 1)
            if jsonEnc:
                fields[3] = json.loads(fields[3])
            jellyfin.doUtils.downloadUrl(fields[1], postBody=fields[3], type=fields[0], json=jsonEnc, authenticate=True)
        else:
            jellyfin.doUtils.downloadUrl(fields[1], type=fields[0], json=jsonEnc, authenticate=True)

    f.close()

    # Change default user password
    url = "{server}/jellyfin/Users/%s/Password" % jellyfin.getUserId()
    data = json.loads("{\"CurrentPassword\":\"%s\",\"NewPw\":\"%s\"}" % (jellyfin.hashPassword(oldpw), password))
    jellyfin.doUtils.downloadUrl(url, postBody=data, type="POST", json=True, authenticate=True)

    # Remove device
    url = "{server}/jellyfin/Devices?Id=%s" % jellyfin.doUtils.deviceId
    jellyfin.doUtils.downloadUrl(url, type="DELETE", json=False, authenticate=True)

if __name__ == "__main__":
    main()


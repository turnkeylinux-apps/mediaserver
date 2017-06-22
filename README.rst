MediaServer - Simple Network Attached Media Storage
===================================================

TurnKey MediaServer makes it easy to bring all of your home videos, music,
and photos together into a single server that automatically converts and
streams your media on-the-fly to play on any device. This app integrates
`Emby`_ with a file management web app, Windows-compatible network file
sharing and other transfer protocols including SFTP, rsync, NFS, and
WebDAV. Files can be managed in private or public storage.

This appliance includes all the standard features in `TurnKey Core`_,
and on top of that:

- SSL support out of the box.

- Media server (`Emby`_) configurations:
   
   - Web UI (https) listening on ports 8096 and 8920 (https).
   - Preconfigured path substitution for Samba access
   - Preconfigured Music, Movies, TVShows, and Photos directories

- File server (`Samba`_) configurations:
   
   - Preconfigured wordgroup: WORKGROUP
   - Preconfigured netbios name: MEDIASERVER
   - Configured Samba and UNIX users/groups synchronization (CLI and
     Webmin).
   - Configured root as administrative samba user.
   - Configured shares:
      
      - Users home directory.
      - Public storage.
      - CD-ROM with automount and umount hooks (/media/cdrom).

- Access your files securely from anywhere via `_WebDAVCGI`_:
   
   - Web GUI access to your files, with online previews of major formats and drag-n-drop
     support.
   - Pre-configured authentication (Samba).
   - Pre-configured repositories (storage, user home directories).

- Default storage: */srv/storage*

- Includes popular compression support (zip, rar, bz2).
- Webmin module for configuring Samba.

Credentials *(passwords set at first boot)*
-------------------------------------------

**File server access**: log in as user **root**

  #. SambaDAV web file management: https://12.34.56.789/

  #. From the command line::

        smbclient //12.34.56.789/storage -Uroot
        mount -t cifs //12.34.56.789/storage /mnt -o username=root,password=PASSWORD

**Emby Web UI**: log in as username **emby**

    #. https://12.34.56.789:8096/
    #. https://12.34.56.789:8920/

-  Webmin, Webshell, SSH, Samba: username **root**

.. _Emby: https://emby.media/
.. _TurnKey Core: https://www.turnkeylinux.org/core
.. _Samba: http://www.samba.org/samba/what_is_samba.html
.. _WebDAVCGI: https://github.com/DanRohde/webdavcgi


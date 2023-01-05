MediaServer - Simple Network Attached Media Storage
===================================================

TurnKey MediaServer makes it easy to bring all of your home videos, music,
and photos together into a single server that automatically converts and
streams your media on-the-fly to play on any device. This app integrates
`Jellyfin`_ with a file management web app, Windows-compatible network file
sharing and other transfer protocols including SFTP, rsync, NFS, and
WebDAV. Files can be managed in private or public storage.

This appliance includes all the standard features in `TurnKey Core`_,
and on top of that:

- SSL support out of the box.

- Media server (`Jellyfin`_) configuration:
   
   - Web UI listening on ports 8096 (http) and 8920 (https - uses Jellyfin's
     own custom SSL/TLS certificate - see more below).
   - Pre-configured reverse proxy to connect to your Jellyfin server via port
     12322 using system SSL/TLS certificates.
   - Pre-configured path substitution for Samba access.
   - Pre-configured Music, Movies, TVShows, and Photos directories.
   - Initial configuration to support hardware video acceleration (VA).
     Additional steps are still required - please see the relevant `Jellyfin
     VA documentation`_. Installation of the specific drivers for your
     hardware will also be required (should be available from Debian
     repositories).

- File server (`Samba`_) configuration:
   
   - Pre-configured wordgroup: WORKGROUP
   - Pre-configured netbios name: MEDIASERVER
   - Configured root as administrative samba user.
   - Configured shares:
      
      - Users home directory.
      - Public storage.
      - CD-ROM with automount and umount hooks (/media/cdrom).

   - NOTE: Due to the removal of libpam-smbpass (see `issue #1188`_), new Samba
     users must have their passwords explictly set separately when created.
     However, if you create a Samba user using smbpasswd, then a new Linux user
     of the same name, with the same password is automatically created
     (including home directory). E.g.::

       # smbpasswd -a new_user
       New SMB password:
       Retype new SMB password:
       Added user new_user.
       # ls /home/
       new_user

- Webmin module for configuring Samba.
- Includes popular compression support (zip, rar, bz2).
- Includes flip to convert text file endings between UNIX and DOS
  formats.
- `WebDAV CGI`_ providing WebUI and WebDAV access.

- Access your files securely from anywhere via `WebDAV CGI`_:
   
   - Web GUI access to your files, with online previews of major formats and drag-n-drop
     support.
   - Pre-configured authentication (Samba).
   - Pre-configured repositories (storage, user home directories).

- Default storage: */srv/storage*
- Accessing file server via samba on the command line::

    smbclient //1.0.0.61/storage -Uroot
    mount -t cifs //1.0.0.61/storage /mnt -o username=root,password=PASSWORD

- You can generate your own PKCS #12 certificate (required for direct
  connection to Jellyfin via HTTPS)::

    mkdir /etc/ssl/jellyfin
    SSL_PASSWORD=YOUR_PASSWORD
    CERT_PATH=/etc/ssl/jellyfin/cert.pfx
    openssl pkcs12 -export -out $CERT_PATH -inkey /etc/ssl/private/cert.key -in /etc/ssl/private/cert.pem -password pass:$SSL_PASSWORD
    chmod +r $CERT_PATH
    JELLYFIN_CONF=/etc/jellyfin/system.xml
    sed -i '/<CertificatePath*/d' $JELLYFIN_CONF
    sed -i '/<CertificatePassword*/d' $JELLYFIN_CONF
    sed -i "/<\/ServerConfiguration/i \ <CertificatePath>$CERT_PATH</CertificatePath>\n <CertificatePassword>$SSL_PASSWORD</CertificatePassword>" $JELLYFIN_CONF

Credentials *(passwords set at first boot)*
-------------------------------------------

-  Jellyfin webUI: username **jellyfin**
-  Webmin, Webshell, SSH, Samba: username **root**
-  Web based file manager (WebDAV CGI):
   
   - username **root** (or Samba users)

.. _Jellyfin: https://jellyfin.media/
.. _TurnKey Core: https://www.turnkeylinux.org/core
.. _Jellyfin VA documentation: https://jellyfin.org/docs/general/administration/hardware-acceleration.html#configuring-vaapi-acceleration-on-debianubuntu-from-deb-packages
.. _Samba: https://www.samba.org/samba/what_is_samba.html
.. _issue #1188: https://github.com/turnkeylinux/tracker/issues/1188
.. _WebDAV CGI: https://github.com/DanRohde/webdavcgi


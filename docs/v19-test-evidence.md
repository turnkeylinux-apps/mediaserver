# MediaServer v19 candidate evidence

## Candidate boundary

The candidate uses Jellyfin's signed Debian 13 stable repository and current
HTTP APIs for initial administrator creation, first-boot password replacement,
library configuration, authenticated scan inspection, and playback metadata.
The Apache configuration uses the current `/socket` websocket endpoint and
Apache 2.4 authorization syntax.

The focused test is `tests/v19.sh`. It covers the normal appliance path:
administrator login, the four preconfigured media directories, a tiny media
scan, playback metadata, the systemd service, direct API access, TLS proxy
access, and the signed updater check and dry run.

## Verification state

Exact run `20260826t155731z-1143-18806` passed at source
`d075b5651852cac080a7bd28fe8c4d3e2e189cc4`. It built and imported the Trixie
root, completed boot and firstboot, authenticated with the configured Jellyfin
administrator, verified the four libraries, indexed generated audio, obtained
playback metadata, exercised direct and proxied APIs, checked service state,
and resolved the signed updater check and dry run. The retained report SHA-256
is `5e8c6806648517a83985f365a413636b819a9722894a1601b1b19d5b620562f9`.

Product-fix loops used: 2 of 3. The fixes keep the firstboot password out of
process arguments and wait for the Jellyfin startup API before configuring the
server. Readiness-log suppression and removal of an unused PHP configuration
pass were acceptance-path corrections and consumed zero product loops.

## Deferred coverage

- MEDIUM: Hardware-accelerated transcoding depends on the host GPU, device
  passthrough, and matching Debian drivers. The acceptance path checks media
  discovery and playback metadata without asserting host-specific acceleration.
- MEDIUM: Direct Jellyfin HTTPS on port 8920 requires the administrator to add
  a custom PKCS #12 certificate. The appliance-managed TLS proxy on port 12322
  is the v19 acceptance path.
- LOW: The API test proves administrator authentication and the web server path
  without browser-driven user-interface automation.

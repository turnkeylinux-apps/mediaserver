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

Static shell parsing, Python compilation, source-contract checks, executable
mode checks, result-schema checks, and whitespace checks are the candidate
gates. An exact appliance run is intentionally left for the independent Wave 2
runner because the shared runner currently has a known private-source cleanup
dependency failure. This is an infrastructure boundary and consumes zero
product-fix loops.

Product-fix loops used: 0 of 3.

## Deferred coverage

- MEDIUM: Hardware-accelerated transcoding depends on the host GPU, device
  passthrough, and matching Debian drivers. The acceptance path checks media
  discovery and playback metadata without asserting host-specific acceleration.
- MEDIUM: Direct Jellyfin HTTPS on port 8920 requires the administrator to add
  a custom PKCS #12 certificate. The appliance-managed TLS proxy on port 12322
  is the v19 acceptance path.
- LOW: The API test proves administrator authentication and the web server path
  without browser-driven user-interface automation.

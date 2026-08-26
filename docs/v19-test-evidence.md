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
access, and a signed real updater apply from the retained official
`10.11.10+deb13` package to `10.11.11+deb13`. After the update it waits for the
API and proves a fresh administrator login, libraries, indexed media bytes,
item identity, and recorded source provenance survived.

## Verification state

Static shell parsing, Python syntax parsing, source-contract checks, executable
mode checks, result-schema checks, credential-boundary checks, and whitespace
checks pass. Exact run `20260826t151619z-3628585-319` passed against commit
`9d1729b1f4acf8113000b667c853de37ef423ae5` and source archive SHA-256
`4d4dbdef83d594313c3812f65a029fd908022c54375fee5926dc709fefe09db4`.
Its report SHA-256 is
`6ec1845dccd1a17cd49f726e4721ed3c9e30684ddce2b6878ed231c65a7f3b80`,
and all eight retained `SHA256SUMS` entries verify.

Product-fix loops used: 1 of 6. Test and evidence corrections consume zero.

The first exact run (`20260826t115503z-2240736-11770`) reproduced a product
startup race: Jellyfin 10.11.11 returned ready from `/health`, then returned
HTTP 503 from the real `/Startup/Configuration` bootstrap API. Product loop 1
keeps the health gate and boundedly retries that configuration request for up
to four minutes. A terminal failure now includes the last 100 lines of
Jellyfin's build log. The correction passed the final exact run.

Run `20260826t142710z-3357561-31407` is explicitly rejected as acceptance
evidence: `/run` denied direct execution of the nested updater fixture, while
the outer script lacked explicit strict mode and emitted a false PASS with an
empty updater candidate. Commit `d672d5d` made the outer script fail closed and
invoked the nested fixture through Bash. Its next run,
`20260826t145556z-3503328-12261`, correctly failed without a result when the
public API transiently returned HTTP 503 immediately after firstboot. The
validation-only readiness gate in `9d1729b` boundedly waits for valid direct and
proxied API version documents. Neither test correction consumes a product loop.

The final PASS retained a nonempty child result proving an actual signed
package downgrade to `10.11.10+deb13`, updater check/apply to
`10.11.11+deb13`, fresh administrator login, all four libraries, identical
indexed media bytes and identity, and unchanged non-version source provenance.

The exact command is:

```sh
TKLDEV_CONTAINER=tkldev19-wave2 \
TKL_HARNESS_STATE_DIR=/home/agent/.local/state/turnkey-v19-harness-wave2 \
TKL_HARNESS_LOCK_FILE=/home/agent/.local/state/turnkey-v19-harness-wave2/build.lock \
TKL_HARNESS_LOCK_TIMEOUT=3600 \
TKL_HARNESS_DOCKER_LIMIT_BYTES=53687091200 \
/home/agent/turnkey/tools/test-v19-appliance mediaserver \
  --source /home/agent/.local/worktrees/turnkey-apps/mediaserver/wish-mediaserver-v19-trixie
```

The acceptance test consumes the firstboot password through
`TKL_TEST_APP_PASS`, verifies the one-time bootstrap credential was removed,
and writes the seven-key result record to `TKL_TEST_RESULT` for retention by
the exact harness.

## Deferred coverage

- MEDIUM: Hardware-accelerated transcoding depends on the host GPU, device
  passthrough, and matching Debian drivers. The acceptance path checks media
  discovery and playback metadata without asserting host-specific acceleration.
- MEDIUM: Direct Jellyfin HTTPS on port 8920 requires the administrator to add
  a custom PKCS #12 certificate. The appliance-managed TLS proxy on port 12322
  is the v19 acceptance path.
- LOW: The API test proves administrator authentication and the web server path
  without browser-driven user-interface automation.

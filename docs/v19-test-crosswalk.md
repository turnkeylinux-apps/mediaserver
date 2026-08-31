# MediaServer v19 acceptance crosswalk

| Criterion | Acceptance proof |
| --- | --- |
| Official Trixie package source | Check the recorded repository, suite, signing fingerprint, installed dpkg version, and Jellyfin public API version. |
| Administrator login | Require removal of the one-time bootstrap credential, authenticate the `jellyfin` administrator through `Users/AuthenticateByName` with `TKL_TEST_APP_PASS`, and retain the returned access token for protected API requests. |
| Media library | Verify all four default library paths, add a one-second synthetic audio file, request a scan, and find the indexed item by its exact path. |
| Playback metadata | Request playback information for the indexed item and require a playable media-source identifier and an audio stream. |
| Web and reverse proxy | Read the public system information through direct HTTP and the appliance TLS reverse proxy, then compare their Jellyfin versions. |
| Service supervision | Require the `jellyfin` systemd unit to be enabled and active. |
| Signed update channel | Downgrade the disposable runtime to the retained official `10.11.10+deb13` packages, run the actual helper to install `10.11.11+deb13`, wait for the API, then prove fresh administrator login, the same indexed item, all libraries, media bytes, and source provenance survived. |
| Machine-readable result | Emit exactly the seven v19 result keys after every preceding assertion succeeds. |

The test generates its audio fixture locally with Jellyfin's packaged ffmpeg
binary, so library and playback metadata proof does not depend on a network
media source.

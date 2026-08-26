#!/bin/bash -e

set -o pipefail

SOURCE_RECORD=/usr/local/share/turnkey-mediaserver/source
UPDATER=/usr/local/sbin/turnkey-mediaserver-update
AUTHORIZATION='MediaBrowser Client="TurnKey v19 test", Device="Acceptance", DeviceId="turnkey-v19", Version="19"'
FIXTURE='/srv/storage/Music/Wave 2 Acceptance Tone.mp3'

cleanup() {
    rm -f "$FIXTURE"
}
trap cleanup EXIT

[ -s "$SOURCE_RECORD" ]
grep -qx 'repository=https://repo.jellyfin.org/debian' "$SOURCE_RECORD"
grep -qx 'suite=trixie' "$SOURCE_RECORD"
grep -qx 'signing_fingerprint=4918AABC486CA052358D778D49023CD01DE21A7B' \
    "$SOURCE_RECORD"

installed=$(dpkg-query -W -f='${Version}' jellyfin)
dpkg --compare-versions "$installed" ge '10.11.11+deb13'
[ "$(awk -F= '$1 == "installed_version" {print $2}' "$SOURCE_RECORD")" = \
    "$installed" ]
systemctl is-active --quiet jellyfin
systemctl is-enabled --quiet jellyfin

public_info=$(curl -fsS http://127.0.0.1:8096/System/Info/Public)
proxy_info=$(curl -fkSs https://127.0.0.1:12322/System/Info/Public)
api_version=$(jq -er '.Version' <<<"$public_info")
[ "$api_version" = "${installed%%+*}" ]
[ "$(jq -er '.Version' <<<"$proxy_info")" = "$api_version" ]

[ ! -e /etc/jellyfin/turnkey-bootstrap-password ]
password=${TKL_TEST_APP_PASS:?missing exact-harness application password}
authentication=$(curl -fsS -X POST \
    http://127.0.0.1:8096/Users/AuthenticateByName \
    -H "X-Emby-Authorization: $AUTHORIZATION" \
    -H 'Content-Type: application/json' \
    --data "$(jq -n --arg username jellyfin --arg password "$password" \
        '{Username:$username,Pw:$password}')")
unset password
token=$(jq -er '.AccessToken' <<<"$authentication")
user_id=$(jq -er '.User.Id' <<<"$authentication")

virtual_folders=$(curl -fsS http://127.0.0.1:8096/Library/VirtualFolders \
    -H "X-Emby-Authorization: $AUTHORIZATION" \
    -H "X-Emby-Token: $token")
for path in \
    /srv/storage/Music \
    /srv/storage/Movies \
    /srv/storage/TVShows \
    /srv/storage/Photos; do
    jq -e --arg path "$path" \
        'any(.[]; any(.Locations[]?; . == $path))' \
        <<<"$virtual_folders" >/dev/null
done

/usr/lib/jellyfin-ffmpeg/ffmpeg -nostdin -loglevel error \
    -f lavfi -i 'sine=frequency=880:duration=1' \
    -metadata title='Wave 2 Acceptance Tone' -y "$FIXTURE"
chown jellyfin:users "$FIXTURE"
curl -fsS -X POST http://127.0.0.1:8096/Library/Refresh \
    -H "X-Emby-Authorization: $AUTHORIZATION" \
    -H "X-Emby-Token: $token" >/dev/null

item_id=
for attempt in $(seq 1 60); do
    items=$(curl -fsS -G http://127.0.0.1:8096/Items \
        -H "X-Emby-Authorization: $AUTHORIZATION" \
        -H "X-Emby-Token: $token" \
        --data-urlencode 'Recursive=true' \
        --data-urlencode 'IncludeItemTypes=Audio' \
        --data-urlencode 'Fields=MediaSources,MediaStreams,Path')
    item_id=$(jq -er --arg path "$FIXTURE" \
        '.Items[]? | select(.Path == $path) | .Id' <<<"$items" 2>/dev/null || true)
    [ -z "$item_id" ] || break
    sleep 2
done
[ -n "$item_id" ]
jq -e --arg id "$item_id" \
    '.Items[] | select(.Id == $id) |
     (.MediaSources[0].Path | length > 0) and
     any(.MediaStreams[]; .Type == "Audio")' <<<"$items" >/dev/null

playback=$(curl -fsS -X POST \
    "http://127.0.0.1:8096/Items/$item_id/PlaybackInfo?userId=$user_id" \
    -H "X-Emby-Authorization: $AUTHORIZATION" \
    -H "X-Emby-Token: $token" \
    -H 'Content-Type: application/json' \
    --data '{"StartTimeTicks":0,"IsPlayback":true,"AutoOpenLiveStream":false}')
jq -e '.MediaSources[0].Id | length > 0' <<<"$playback" >/dev/null

updater_check=$($UPDATER --check)
candidate=$(awk -F= '$1 == "candidate" {print $2}' <<<"$updater_check")
[ -n "$candidate" ]
grep -qx 'status=up-to-date' <<<"$updater_check"
grep -qx 'apply=dry-run signed package transaction' \
    < <($UPDATER --apply --dry-run)

if [ -n "${TKL_TEST_RESULT:-}" ]; then
    cat > "$TKL_TEST_RESULT" <<EOF
package_source=official Jellyfin stable APT repository for Debian 13
installed_version=$installed
runtime_checks=admin API login, direct web API, TLS reverse proxy, four default libraries, audio scan, playback metadata, systemd service
updater_command=turnkey-mediaserver-update --check; turnkey-mediaserver-update --apply --dry-run
updater_result=up-to-date candidate $candidate; signed dry-run transaction accepted
updater_channel=official Jellyfin stable APT packages for Debian 13
integrity_evidence=APT key fingerprint 4918AABC486CA052358D778D49023CD01DE21A7B and dpkg installed package version
EOF
fi

echo "PASS: Jellyfin $installed login, library scan, playback metadata, proxy, and updater"

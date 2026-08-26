#!/bin/bash -e

set -o pipefail

SOURCE_RECORD=/usr/local/share/turnkey-mediaserver/source
UPDATER=/usr/local/sbin/turnkey-mediaserver-update
TEST_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
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
systemctl is-active --quiet smbd
grep -Eq '^[[:space:]]*netbios name = MEDIASERVER$' /etc/samba/smb.conf
grep -Eq '^[[:space:]]*path = /srv/storage$' /etc/samba/smb.conf
grep -q "'MEDIASERVER' =>" /var/www/webdavcgi/webdav.conf
id -nG jellyfin | tr ' ' '\n' | grep -qx users
id -nG jellyfin | tr ' ' '\n' | grep -qx video
command -v vainfo >/dev/null

public_info=$(curl -fsS http://127.0.0.1:8096/System/Info/Public)
proxy_info=$(curl -fkSs https://127.0.0.1:12322/System/Info/Public)
api_version=$(jq -er '.Version' <<<"$public_info")
[ "$api_version" = "${installed%%+*}" ]
[ "$(jq -er '.Version' <<<"$proxy_info")" = "$api_version" ]

[ ! -e /etc/jellyfin/turnkey-bootstrap-password ]
password=${TKL_TEST_APP_PASS:?missing exact-harness application password}
authentication=$(jq -n --arg username jellyfin --arg password "$password" \
    '{Username:$username,Pw:$password}' |
    curl -fsS -X POST \
        http://127.0.0.1:8096/Users/AuthenticateByName \
        -H "X-Emby-Authorization: $AUTHORIZATION" \
        -H 'Content-Type: application/json' --data-binary @-)
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

updater_fixture=$("$TEST_DIR/updater-apply-fixture.sh" "$FIXTURE")
grep -qx 'fixture_from=10.11.10+deb13' <<<"$updater_fixture"
grep -qx 'fixture_to=10.11.11+deb13' <<<"$updater_fixture"
grep -qx \
    'fixture_result=admin re-login, four libraries, indexed media, and source provenance survived actual updater apply' \
    <<<"$updater_fixture"
candidate=$(awk -F= '$1 == "fixture_to" {print $2}' <<<"$updater_fixture")

if [ -n "${TKL_TEST_RESULT:-}" ]; then
    cat > "$TKL_TEST_RESULT" <<EOF
package_source=official Jellyfin stable APT repository for Debian 13
installed_version=$installed
runtime_checks=admin API login, direct web API, TLS reverse proxy, four default libraries, audio scan, playback metadata, Jellyfin and Samba services, MediaServer shared-storage configuration, post-update admin re-login and data persistence
updater_command=disposable official package downgrade to 10.11.10+deb13; turnkey-mediaserver-update --check; turnkey-mediaserver-update --apply
updater_result=actual signed package update to $candidate; admin, library, media, and source provenance preserved
updater_channel=official Jellyfin stable APT packages for Debian 13
integrity_evidence=APT signature with key fingerprint 4918AABC486CA052358D778D49023CD01DE21A7B, exact dpkg versions, unchanged source provenance, and unchanged media SHA256 across the real update
EOF
fi

echo "PASS: Jellyfin $installed login, media, proxy, and real 10.11.10 to 10.11.11 updater apply"

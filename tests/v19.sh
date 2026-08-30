#!/bin/bash

set -Eeuo pipefail
shopt -s inherit_errexit

result=${TKL_TEST_RESULT:?TKL_TEST_RESULT is required}
app_password=${TKL_TEST_APP_PASS:?TKL_TEST_APP_PASS is required}
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
[ ! -e /etc/jellyfin/turnkey-bootstrap-password ]
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

api_ready=false
for attempt in $(seq 1 120); do
    public_info=$(curl -fsS http://127.0.0.1:8096/System/Info/Public \
        2>/dev/null || true)
    proxy_info=$(curl -fkSs https://127.0.0.1:12322/System/Info/Public \
        2>/dev/null || true)
    if jq -e '.Version | length > 0' <<<"$public_info" >/dev/null 2>&1 &&
            jq -e '.Version | length > 0' <<<"$proxy_info" >/dev/null 2>&1; then
        api_ready=true
        break
    fi
    sleep 2
done
[ "$api_ready" = true ]
api_version=$(jq -er '.Version' <<<"$public_info")
[ "$api_version" = "${installed%%+*}" ]
[ "$(jq -er '.Version' <<<"$proxy_info")" = "$api_version" ]

authentication=$(curl -fsS -X POST \
    http://127.0.0.1:8096/Users/AuthenticateByName \
    -H "X-Emby-Authorization: $AUTHORIZATION" \
    -H 'Content-Type: application/json' \
    --data "$(jq -n --arg username jellyfin --arg password "$app_password" \
        '{Username:$username,Pw:$password}')")
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

updater_fixture=$(bash "$TEST_DIR/updater-apply-fixture.sh" "$FIXTURE")
grep -qx 'fixture_from=10.11.10+deb13' <<<"$updater_fixture"
grep -qx 'fixture_to=10.11.11+deb13' <<<"$updater_fixture"
grep -qx \
    'fixture_result=admin re-login, four libraries, indexed media, and source provenance survived actual updater apply' \
    <<<"$updater_fixture"
candidate=$(awk -F= '$1 == "fixture_to" {print $2}' <<<"$updater_fixture")

{
    echo 'package_source=official Jellyfin stable APT repository for Debian 13'
    echo "installed_version=$installed"
    echo 'runtime_checks=firstboot secret removal, admin API login, direct web API, TLS reverse proxy, four default libraries, shared Samba/WebDAV storage identity, audio scan, playback metadata, systemd supervision and restart'
    echo 'updater_command=turnkey-mediaserver-update --check; turnkey-mediaserver-update --apply'
    echo "updater_result=signed actual package update 10.11.10+deb13 to $candidate; admin re-login, four libraries, indexed media, and source provenance persisted"
    echo 'updater_channel=official Jellyfin stable APT packages for Debian 13'
    echo 'integrity_evidence=APT key fingerprint 4918AABC486CA052358D778D49023CD01DE21A7B and dpkg installed package version'
} > "$result"

#!/bin/bash

set -Eeuo pipefail
shopt -s inherit_errexit

SOURCE_RECORD=/usr/local/share/turnkey-mediaserver/source
UPDATER=/usr/local/sbin/turnkey-mediaserver-update
AUTHORIZATION='MediaBrowser Client="TurnKey v19 updater test", Device="Acceptance", DeviceId="turnkey-v19-updater", Version="19"'
FROM_VERSION=10.11.10+deb13
TO_VERSION=10.11.11+deb13
JELLYFIN_BASE=http://127.0.0.1:8096
PIN=/etc/apt/preferences.d/jellyfin-v19-updater-fixture.pref
MEDIA_FIXTURE=${1:?usage: updater-apply-fixture.sh MEDIA_PATH}

cleanup() {
    rm -f "$PIN"
}
trap cleanup EXIT

[ "$(id -u)" -eq 0 ]
[ -x "$UPDATER" ]
[ -s "$SOURCE_RECORD" ]
[ -s "$MEDIA_FIXTURE" ]
password=${TKL_TEST_APP_PASS:?missing exact-harness application password}

wait_for_version() {
    local expected=${1%%+*}
    local attempt public_info
    for attempt in $(seq 1 120); do
        if public_info=$(curl -fsS --connect-timeout 2 --max-time 5 \
                "$JELLYFIN_BASE/System/Info/Public" 2>/dev/null) &&
                [ "$(jq -er '.Version' <<<"$public_info")" = "$expected" ]; then
            return 0
        fi
        sleep 2
    done
    journalctl -u jellyfin --no-pager -n 100 >&2 || true
    return 1
}

authenticate() {
    jq -n --arg username jellyfin --arg password "$password" \
        '{Username:$username,Pw:$password}' |
        curl -fsS -X POST "$JELLYFIN_BASE/Users/AuthenticateByName" \
            -H "X-Emby-Authorization: $AUTHORIZATION" \
            -H 'Content-Type: application/json' --data-binary @-
}

assert_package_set() {
    local expected=$1
    local package
    for package in jellyfin jellyfin-server jellyfin-web; do
        [ "$(dpkg-query -W -f='${Version}' "$package")" = "$expected" ]
    done
}

verify_media_state() {
    local token=$1
    local virtual_folders path items item_id
    virtual_folders=$(curl -fsS "$JELLYFIN_BASE/Library/VirtualFolders" \
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

    items=$(curl -fsS -G "$JELLYFIN_BASE/Items" \
        -H "X-Emby-Authorization: $AUTHORIZATION" \
        -H "X-Emby-Token: $token" \
        --data-urlencode 'Recursive=true' \
        --data-urlencode 'IncludeItemTypes=Audio' \
        --data-urlencode 'Fields=MediaSources,MediaStreams,Path')
    item_id=$(jq -er --arg path "$MEDIA_FIXTURE" \
        '.Items[]? | select(.Path == $path) | .Id' <<<"$items")
    jq -e --arg id "$item_id" \
        '.Items[] | select(.Id == $id) |
         (.MediaSources[0].Path | length > 0) and
         any(.MediaStreams[]; .Type == "Audio")' <<<"$items" >/dev/null
    printf '%s\n' "$item_id"
}

apt-get -o Acquire::https::proxy=false update >/dev/null
for package in jellyfin jellyfin-server jellyfin-web; do
    apt-cache madison "$package" |
        awk -v version="$FROM_VERSION" '$3 == version {found=1} END {exit !found}'
    apt-cache madison "$package" |
        awk -v version="$TO_VERSION" '$3 == version {found=1} END {exit !found}'
done

installed=$(dpkg-query -W -f='${Version}' jellyfin)
[ "$installed" = "$TO_VERSION" ]
assert_package_set "$TO_VERSION"
[ "$(apt-cache policy jellyfin | awk '/Candidate:/ {print $2; exit}')" = \
    "$TO_VERSION" ]
provenance_before=$(grep -v '^installed_version=' "$SOURCE_RECORD" | sha256sum |
    awk '{print $1}')
media_sha_before=$(sha256sum "$MEDIA_FIXTURE" | awk '{print $1}')

cat > "$PIN" <<EOF
Package: jellyfin jellyfin-server jellyfin-web
Pin: version $TO_VERSION
Pin-Priority: 1002
EOF

DEBIAN_FRONTEND=noninteractive apt-get \
    -o Acquire::https::proxy=false -y --allow-downgrades install \
    "jellyfin=$FROM_VERSION" \
    "jellyfin-server=$FROM_VERSION" \
    "jellyfin-web=$FROM_VERSION" >/dev/null
assert_package_set "$FROM_VERSION"
sed -i "s/^installed_version=.*/installed_version=$FROM_VERSION/" \
    "$SOURCE_RECORD"
systemctl restart jellyfin
wait_for_version "$FROM_VERSION"

authentication=$(authenticate)
from_token=$(jq -er '.AccessToken' <<<"$authentication")
from_item_id=$(verify_media_state "$from_token")

updater_check=$($UPDATER --check)
grep -qx "installed=$FROM_VERSION" <<<"$updater_check"
grep -qx "candidate=$TO_VERSION" <<<"$updater_check"
grep -qx 'channel=official Jellyfin stable APT packages for Debian 13' \
    <<<"$updater_check"
grep -qx \
    'signing_fingerprint=4918AABC486CA052358D778D49023CD01DE21A7B' \
    <<<"$updater_check"
grep -qx 'status=update-available' <<<"$updater_check"

updater_apply=$($UPDATER --apply)
grep -qx "apply=installed $TO_VERSION" <<<"$updater_apply"
wait_for_version "$TO_VERSION"
assert_package_set "$TO_VERSION"
[ "$(awk -F= '$1 == "installed_version" {print $2}' "$SOURCE_RECORD")" = \
    "$TO_VERSION" ]

authentication=$(authenticate)
to_token=$(jq -er '.AccessToken' <<<"$authentication")
to_item_id=$(verify_media_state "$to_token")
[ "$to_item_id" = "$from_item_id" ]
[ "$(sha256sum "$MEDIA_FIXTURE" | awk '{print $1}')" = "$media_sha_before" ]
[ "$(grep -v '^installed_version=' "$SOURCE_RECORD" | sha256sum | \
    awk '{print $1}')" = "$provenance_before" ]

unset password from_token to_token authentication
printf 'fixture_from=%s\n' "$FROM_VERSION"
printf 'fixture_to=%s\n' "$TO_VERSION"
printf 'fixture_item_id=%s\n' "$to_item_id"
printf '%s\n' \
    'fixture_result=admin re-login, four libraries, indexed media, and source provenance survived actual updater apply'

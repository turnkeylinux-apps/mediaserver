# MediaServer v19 source decision

MediaServer v19 installs Jellyfin from the upstream project's signed stable
APT repository for Debian 13. This keeps the appliance on Jellyfin's supported
Trixie package path and lets normal Debian package tooling handle dependency
resolution and upgrades.

The source contract is:

- repository: `https://repo.jellyfin.org/debian`
- suite: `trixie`
- component: `main`
- signing-key fingerprint: `4918 AABC 486C A052 358D 778D 4902 3CD0 1DE2 1A7B`
- minimum validated package: `jellyfin 10.11.11+deb13`
- corresponding upstream tag: `v10.11.11`
- corresponding upstream commit: `1fbd8739292cce610231be93daf43368733edf63`

The build verifies the dearmored key fingerprint before refreshing package
metadata. It records the installed version, repository, suite, component,
fingerprint, and channel in `/usr/local/share/turnkey-mediaserver/source`.
The updater checks that record, the deb822 source, and the installed key before
querying or applying an update.

The acceptance boundary is the official stable APT channel rather than a
single frozen package. Later signed stable releases remain eligible while the
recorded `10.11.11+deb13` package establishes the v19 migration floor.

Upstream release notes and support are available from the Jellyfin repository.
Security reports belong in Jellyfin's private advisory form at
`https://github.com/jellyfin/jellyfin/security/advisories/new`, not in a public
issue.

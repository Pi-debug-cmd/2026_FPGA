#!/bin/sh
# Install the music-button boot-race hotfix without starting audio.
set -eu

STAGE=${1:?usage: install_world_minphase_hotfix_round30.sh STAGE_DIR}
APP_ROOT=/opt/world_voice_pl
OLD_RELEASE=${APP_ROOT}/releases/20261029_round27
NEW_RELEASE=${APP_ROOT}/releases/20261030_round30
INIT=/etc/init.d/world-voice

expect_sha() {
    expected=$1
    path=$2
    actual=$(sha256sum "${path}" | awk '{print $1}')
    [ "${actual}" = "${expected}" ] || {
        echo "SHA mismatch: ${path}: ${actual} != ${expected}" >&2
        exit 1
    }
}

[ "$(readlink -f "${APP_ROOT}/current")" = "${OLD_RELEASE}" ]
test ! -e "${NEW_RELEASE}"
expect_sha 211392ced7800c5e09db0a9cb8dade1cfe39da939faf3ce1a56e414e795bc499 "${INIT}"
expect_sha cd078393e0e4ab9516c4cd53f401a5d0316310bc8f04dac9b972b662704086d6 "${STAGE}/world_minphase_autostart.sh"
expect_sha f6ed4c877041e94ac8a166d301bf86af132c37d1a4ef0b39fbeaeeddb6b6a823 "${STAGE}/world_minphase_init.sh"
expect_sha 616c40b2a706ed68cc43d96063021ef7bf09a498fde362e00d1a69d1531adaeb "${STAGE}/manifest.sha256"

mkdir "${NEW_RELEASE}"
cp "${OLD_RELEASE}/"* "${NEW_RELEASE}/"
cp "${STAGE}/world_minphase_autostart.sh" "${NEW_RELEASE}/world_minphase_autostart.sh"
cp "${STAGE}/manifest.sha256" "${NEW_RELEASE}/manifest.sha256"
chmod 0755 "${NEW_RELEASE}/world_minphase_autostart.sh"
(cd "${NEW_RELEASE}" && sha256sum -c manifest.sha256)

cp -p "${INIT}" /etc/init.d/world-voice.round29
expect_sha 211392ced7800c5e09db0a9cb8dade1cfe39da939faf3ce1a56e414e795bc499 /etc/init.d/world-voice.round29
cp "${STAGE}/world_minphase_init.sh" "${INIT}.new"
chmod 0755 "${INIT}.new"
mv "${INIT}.new" "${INIT}"

ln -s "${NEW_RELEASE}" "${APP_ROOT}/current.round30"
[ -L "${APP_ROOT}/current" ]
rm "${APP_ROOT}/current"
mv "${APP_ROOT}/current.round30" "${APP_ROOT}/current"
sync

[ "$(readlink -f "${APP_ROOT}/current")" = "${NEW_RELEASE}" ]
expect_sha f6ed4c877041e94ac8a166d301bf86af132c37d1a4ef0b39fbeaeeddb6b6a823 "${INIT}"
(cd "${APP_ROOT}/current" && sha256sum -c manifest.sha256)
echo 'WORLD_MINPHASE_HOTFIX30_OK current=20261030_round30 audio_started=0'

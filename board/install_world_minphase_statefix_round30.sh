#!/bin/sh
# Atomically install the Round30 stale-state fix without restarting audio.
set -eu

NEW_INIT=${1:?usage: install_world_minphase_statefix_round30.sh NEW_INIT}
INIT=/etc/init.d/world-voice
OLD_SHA=f6ed4c877041e94ac8a166d301bf86af132c37d1a4ef0b39fbeaeeddb6b6a823
NEW_SHA=4f70ab031bff21c685ef9fbcc51ef5484cb8878d6d7920dbbccad850f3789489

file_sha() {
    sha256sum "$1" | awk '{print $1}'
}

[ "$(file_sha "${INIT}")" = "${OLD_SHA}" ]
[ "$(file_sha "${NEW_INIT}")" = "${NEW_SHA}" ]

cp -p "${INIT}" /etc/init.d/world-voice.round30a
cp "${NEW_INIT}" "${INIT}.new"
chmod 0755 "${INIT}.new"
mv "${INIT}.new" "${INIT}"
sync

[ "$(file_sha "${INIT}")" = "${NEW_SHA}" ]
echo "WORLD_MINPHASE_STATEFIX30_OK sha=${NEW_SHA} audio_restarted=0"

#!/bin/sh
# Board-side, audio-silent fault injection for persistent boot scripts.
set -eu

BASE=/tmp/codex_world_minphase_boot_fault_20261029
AUTOSTART=${BASE}/world_minphase_autostart.sh
INIT=${BASE}/world_minphase_init.sh
TEST=${BASE}/case

rm -rf "${TEST}"
mkdir -p "${TEST}/app" "${TEST}/boot" "${TEST}/run"
printf 'factory' > "${TEST}/factory.bit"
FACTORY_SHA=$(sha256sum "${TEST}/factory.bit" | awk '{print $1}')
printf '%064d  missing.gz\n' 0 > "${TEST}/boot/manifest.sha256"
printf '%s\n' '#!/bin/sh' \
    'printf '\''%s\n'\'' "$1" >> "${WORLD_PL_FAKE_FACTORY_LOG}"' \
    > "${TEST}/factory.sh"
chmod +x "${TEST}/factory.sh"

set +e
WORLD_PL_APP_DIR="${TEST}/app" \
WORLD_PL_BOOT_DIR="${TEST}/boot" \
WORLD_PL_RUN_DIR="${TEST}/run" \
WORLD_PL_FACTORY_INIT="${TEST}/factory.sh" \
WORLD_PL_FACTORY_BIT="${TEST}/factory.bit" \
WORLD_PL_FACTORY_SHA="${FACTORY_SHA}" \
WORLD_PL_LOG="${TEST}/autostart.log" \
WORLD_PL_FAKE_FACTORY_LOG="${TEST}/factory.log" \
    sh "${AUTOSTART}"
RC=$?
set -e
[ "${RC}" -eq 1 ]
[ "$(cat "${TEST}/boot/DISABLE")" = BOOT_ASSET_HASH ]
[ "$(cat "${TEST}/run/state")" = FALLBACK_FACTORY_BOOT_ASSET_HASH ]
[ "$(cat "${TEST}/factory.log")" = start ]

printf 'MANUAL\n' > "${TEST}/disable"
: > "${TEST}/factory.log"
WORLD_PL_DISABLE="${TEST}/disable" \
WORLD_PL_FACTORY_INIT="${TEST}/factory.sh" \
WORLD_PL_DAEMON="${TEST}/must-not-run" \
WORLD_PL_PIDFILE="${TEST}/pid" \
WORLD_PL_STATE="${TEST}/init-state" \
WORLD_PL_FAKE_FACTORY_LOG="${TEST}/factory.log" \
    sh "${INIT}" start
[ "$(cat "${TEST}/factory.log")" = start ]
[ ! -e "${TEST}/pid" ]

echo 'BOARD_BOOT_FAULT_TEST_PASS cases=2 audio_started=0 fpga_changed=0'

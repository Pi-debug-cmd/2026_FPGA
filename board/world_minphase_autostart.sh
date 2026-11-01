#!/bin/sh
# Persistent WORLD minphase-PL supervisor with automatic factory-v23 fallback.
set -u

APP_DIR=${WORLD_PL_APP_DIR:-/opt/world_voice_pl/current}
BOOT_DIR=${WORLD_PL_BOOT_DIR:-/boot/world_pl}
RUN_DIR=${WORLD_PL_RUN_DIR:-/run/world_minphase}
FACTORY_INIT=${WORLD_PL_FACTORY_INIT:-/etc/init.d/world-voice.factory}
FACTORY_BIT=${WORLD_PL_FACTORY_BIT:-/boot/bit/zynq7020.bit}
LOG=${WORLD_PL_LOG:-/tmp/world_minphase_autostart.log}
STATE=${RUN_DIR}/state
CANDIDATE_SHA=${WORLD_PL_CANDIDATE_SHA:-1bc4b3f8f5e5f1b722b0772b9aad23af3c60579dc3c81c44c8d86b408c429373}
FACTORY_SHA=${WORLD_PL_FACTORY_SHA:-16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61}
CHILD_PID=
STOP_REQUESTED=0
SWITCH_STARTED=0
MUSIC_INIT=${WORLD_PL_MUSIC_INIT:-/etc/init.d/music-button}

write_state() {
    mkdir -p "${RUN_DIR}"
    printf '%s\n' "$1" > "${STATE}"
}

log() {
    printf '%s %s\n' "$1" "$(date -Iseconds 2>/dev/null || date)" >> "${LOG}"
}

stop_child() {
    if [ -n "${CHILD_PID}" ] && kill -0 "${CHILD_PID}" 2>/dev/null; then
        kill -TERM "${CHILD_PID}" 2>/dev/null || true
        wait "${CHILD_PID}" 2>/dev/null || true
    fi
    CHILD_PID=
}

pcm_closed() {
    for node in pcm0p pcm1c; do
        path=/proc/asound/card0/${node}/sub0/status
        [ ! -e "${path}" ] || [ "$(cat "${path}")" = closed ] || return 1
    done
    return 0
}

quiesce_boot_audio() {
    "${MUSIC_INIT}" stop >/dev/null 2>&1 || true
    for proc in /proc/[0-9]*; do
        [ -r "${proc}/comm" ] || continue
        [ "$(cat "${proc}/comm" 2>/dev/null)" = aplay ] || continue
        if grep -q '/opt/hardware_test/test.wav' "${proc}/cmdline" 2>/dev/null; then
            kill "${proc##*/}" 2>/dev/null || true
        fi
    done
    count=0
    while ! pcm_closed && [ "${count}" -lt 50 ]; do
        sleep 0.1
        count=$((count + 1))
    done
    pcm_closed
}

restore_factory() {
    stop_child
    quiesce_boot_audio || true
    if grep -q '^world_minphase_dma ' /proc/modules 2>/dev/null; then
        rmmod world_minphase_dma >> "${LOG}" 2>&1 || true
    fi
    if [ "${SWITCH_STARTED}" -eq 1 ] && [ -f "${RUN_DIR}/binding_journal.json" ]; then
        WORLD_FACTORY_SERVICE="${FACTORY_INIT}" \
            python3 "${APP_DIR}/world_exp_switch.py" --base "${RUN_DIR}" --restore \
            >> "${LOG}" 2>&1 && return 0
    fi
    "${FACTORY_INIT}" start >> "${LOG}" 2>&1 || true
    return 1
}

on_stop() {
    STOP_REQUESTED=1
    log AUTOSTART_STOP_REQUESTED
    restore_factory || true
    write_state STOPPED_FACTORY
    exit 0
}

fail_to_factory() {
    reason=$1
    log "AUTOSTART_FAILURE_${reason}"
    mkdir -p "${BOOT_DIR}"
    printf '%s\n' "${reason}" > "${BOOT_DIR}/DISABLE"
    sync
    restore_factory || true
    write_state "FALLBACK_FACTORY_${reason}"
    exit 1
}

trap on_stop INT TERM HUP
rm -rf "${RUN_DIR}"
mkdir -p "${RUN_DIR}"
write_state STARTING
log AUTOSTART_BEGIN

[ ! -e "${BOOT_DIR}/DISABLE" ] || fail_to_factory DISABLED
quiesce_boot_audio || fail_to_factory MUSIC_BUSY
[ "$(sha256sum "${FACTORY_BIT}" | awk '{print $1}')" = "${FACTORY_SHA}" ] || \
    fail_to_factory FACTORY_HASH
(cd "${BOOT_DIR}" && sha256sum -c manifest.sha256) >> "${LOG}" 2>&1 || \
    fail_to_factory BOOT_ASSET_HASH
gzip -dc "${BOOT_DIR}/world_minphase_swap.bin.gz" > "${RUN_DIR}/world_minphase_swap.bin" || \
    fail_to_factory DECOMPRESS
[ "$(sha256sum "${RUN_DIR}/world_minphase_swap.bin" | awk '{print $1}')" = "${CANDIDATE_SHA}" ] || \
    fail_to_factory CANDIDATE_HASH

ln -sf "${APP_DIR}/world_budget_v24" "${RUN_DIR}/world_budget_v24"
ln -sf "${APP_DIR}/world_live_manifest_v21.json" "${RUN_DIR}/world_live_manifest_v21.json"
WORLD_FACTORY_SERVICE="${FACTORY_INIT}" \
    python3 "${APP_DIR}/world_exp_switch.py" --base "${RUN_DIR}" --prepare \
    >> "${LOG}" 2>&1 || fail_to_factory PREPARE
SWITCH_STARTED=1
WORLD_FACTORY_SERVICE="${FACTORY_INIT}" \
    python3 "${APP_DIR}/world_exp_switch.py" --base "${RUN_DIR}" \
    --load "${RUN_DIR}/world_minphase_swap.bin" --sha256 "${CANDIDATE_SHA}" \
    >> "${LOG}" 2>&1 || fail_to_factory FPGA_LOAD
insmod "${APP_DIR}/world_minphase_dma.ko" >> "${LOG}" 2>&1 || fail_to_factory MODULE
[ -c /dev/world_minphase ] || fail_to_factory DEVICE
[ "$(cat /sys/class/fpga_manager/fpga0/state)" = operating ] || fail_to_factory FPGA_STATE
write_state READY_CANDIDATE
log AUTOSTART_READY

while [ "${STOP_REQUESTED}" -eq 0 ]; do
    WORLD_MINPHASE=pl WORLD_EXP=cpu \
        python3 "${APP_DIR}/live_world_trial.py" --base "${RUN_DIR}" --run \
        --seconds 600 --prefill-ms 200 --alsa-period 512 \
        --capture-buffer 4096 --playback-buffer 3072 --start-delay-us 32000 \
        --output-gain-q16 16384 --input-gain-q16 262144 --fifo-io \
        --prompt-tone --ready-delay-s 2 >> "${LOG}" 2>&1 &
    CHILD_PID=$!
    wait "${CHILD_PID}"
    rc=$?
    CHILD_PID=
    [ "${STOP_REQUESTED}" -eq 0 ] || break
    [ "${rc}" -eq 0 ] || fail_to_factory "RUNTIME_${rc}"
    log AUTOSTART_ROUND_OK
done

on_stop

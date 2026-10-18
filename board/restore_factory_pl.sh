#!/bin/sh
# Volatile rollback of the 2026-10-10 candidate; never writes boot files.
set -eu
RUN=/tmp/codex_pl_trial_20261010
# This recovery is tied to the listener paused during the original trial.
# Refuse before changing hardware if reboot has invalidated that process ID.
case "$(tr '\000' ' ' < /proc/551/cmdline 2>/dev/null)" in
    *music-button-listener.sh*) ;;
    *) echo TRIAL_LISTENER_CHANGED_RECHECK_SWITCH_STATE >&2; exit 2;;
esac
test "$(sha256sum "$RUN/factory_restore_swap.bin" | cut -d ' ' -f 1)" = af275946c15ae958e9bed16c12f6cab45b63ebecc18645cec24176315db7fc60
for node in /proc/asound/card0/pcm1c/sub0/status /proc/asound/card0/pcm0p/sub0/status; do
    test "$(cat "$node")" = closed
done
unbind() {
    dev=$1
    if test -L "/sys/bus/platform/devices/$dev/driver"; then
        drv=$(basename "$(readlink "/sys/bus/platform/devices/$dev/driver")")
        echo "UNBIND=$drv:$dev"
        echo "$dev" > "/sys/bus/platform/drivers/$drv/unbind"
    fi
}
bind() {
    drv=$1 dev=$2
    if ! test -L "/sys/bus/platform/devices/$dev/driver"; then
        echo "BIND=$drv:$dev"
        if ! echo "$dev" > "/sys/bus/platform/drivers/$drv/bind"; then
            sleep 1
        fi
    fi
    test "$(basename "$(readlink "/sys/bus/platform/devices/$dev/driver")")" = "$drv"
}
rmmod pitch_dma_proxy
rmdir /sys/kernel/config/device-tree/overlays/codex_pitch_dma_20261010
test ! -e /sys/bus/platform/devices/40400000.dma
for dev in xlnx_snd_card.0.auto 43c40000.audio_formatter 43c50000.i2s_receiver 43c60000.i2s_transmitter 43c20000.axi_dynclk; do
    unbind "$dev"
done
oldpath=$(cat /sys/module/firmware_class/parameters/path)
trap 'printf "%s" "$oldpath" > /sys/module/firmware_class/parameters/path' EXIT
printf "%s" "$RUN" > /sys/module/firmware_class/parameters/path
echo 0 > /sys/class/fpga_manager/fpga0/flags
echo factory_restore_swap.bin > /sys/class/fpga_manager/fpga0/firmware
test "$(cat /sys/class/fpga_manager/fpga0/state)" = operating
echo FACTORY_PL_LOADED
bind gpio-xilinx 41210000.gpio
bind dglnt-dynclk 43c20000.axi_dynclk
bind dglnt-dynclk 43c90000.axi_dynclk
bind xlnx_i2s 43c50000.i2s_receiver
bind xlnx_i2s 43c60000.i2s_transmitter
bind xlnx_formatter_pcm 43c40000.audio_formatter
bind xlnx_snd_card xlnx_snd_card.0.auto
bind xiic-i2c 41600000.i2c
bind uartlite 42c00000.serial
bind xilinx-vtc 43c00000.v_tc
bind xlnx,bridge-vtc 43c80000.v_tc
bind xilinx-frmbuf 43c70000.v_frmbuf_rd
bind xilinx-frmbuf 43ca0000.v_frmbuf_rd
bind xilinx-frmbuf 43cb0000.v_frmbuf_wr
bind xlnx-pl-disp amba_pl:drm_pl_disp_hdmi
bind xlnx-drm xlnx-drm.0
# Hot rebind blocked the serial shell on the tested factory kernel.
# Restore this consumer through a cold boot, not another bind attempt.
echo CAMERA_REQUIRES_COLD_BOOT
bind gpio-keys gpio-keys
alsactl -f "$RUN/mixer_before_pl.state" restore 0
case "$(tr '\000' ' ' < /proc/551/cmdline)" in
    *music-button-listener.sh*) kill -CONT 551;;
    *) echo LISTENER_ID_CHANGED >&2; exit 2;;
esac
echo FACTORY_CORE_ROLLBACK_COMPLETED
echo FULL_PERIPHERAL_RECOVERY_REQUIRES_COLD_BOOT

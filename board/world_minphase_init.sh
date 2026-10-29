#!/bin/sh
### BEGIN INIT INFO
# Provides:          world-voice
# Required-Start:    $local_fs
# Required-Stop:     $local_fs
# Default-Start:     5
# Default-Stop:      0 1 6
# Short-Description: Start WORLD fused-minphase PL with factory-v23 fallback
### END INIT INFO

DAEMON=${WORLD_PL_DAEMON:-/opt/world_voice_pl/current/world_minphase_autostart.sh}
FACTORY=${WORLD_PL_FACTORY_INIT:-/etc/init.d/world-voice.factory}
PIDFILE=${WORLD_PL_PIDFILE:-/var/run/world-voice-pl.pid}
STATE=${WORLD_PL_STATE:-/run/world_minphase/state}
DISABLE=${WORLD_PL_DISABLE:-/boot/world_pl/DISABLE}

start_factory() {
    "${FACTORY}" start
}

case "$1" in
    start)
        if [ -e "${DISABLE}" ]; then
            echo "world-minphase disabled; starting factory v23"
            start_factory
            exit $?
        fi
        if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
            echo "world-minphase already running"
            exit 0
        fi
        "${FACTORY}" stop >/dev/null 2>&1 || true
        rm -f "${PIDFILE}"
        start-stop-daemon -S -b -m -p "${PIDFILE}" -x "${DAEMON}"
        count=0
        while [ "${count}" -lt 300 ]; do
            state=$(cat "${STATE}" 2>/dev/null || true)
            case "${state}" in
                READY_CANDIDATE)
                    echo "world-minphase candidate ready pid=$(cat "${PIDFILE}")"
                    exit 0
                    ;;
                FALLBACK_FACTORY_*|HARD_FAIL_*)
                    echo "world-minphase failed: ${state}; factory v23 selected"
                    exit 1
                    ;;
            esac
            if ! kill -0 "$(cat "${PIDFILE}" 2>/dev/null)" 2>/dev/null; then
                echo "world-minphase supervisor exited before ready"
                start_factory
                exit 1
            fi
            sleep 0.1
            count=$((count + 1))
        done
        echo "world-minphase readiness timeout; selecting factory v23"
        printf '%s\n' TIMEOUT > "${DISABLE}"
        "$0" stop
        start_factory
        exit 1
        ;;
    stop)
        if [ -f "${PIDFILE}" ]; then
            pid=$(cat "${PIDFILE}")
            start-stop-daemon -K -p "${PIDFILE}" -s TERM >/dev/null 2>&1 || true
            count=0
            while kill -0 "${pid}" 2>/dev/null && [ "${count}" -lt 200 ]; do
                sleep 0.1
                count=$((count + 1))
            done
            kill -KILL "${pid}" 2>/dev/null || true
            rm -f "${PIDFILE}"
        else
            "${FACTORY}" stop >/dev/null 2>&1 || true
        fi
        echo "world-voice stopped"
        ;;
    restart)
        "$0" stop
        sleep 1
        "$0" start
        ;;
    status)
        if [ -f "${PIDFILE}" ] && kill -0 "$(cat "${PIDFILE}")" 2>/dev/null; then
            echo "world-minphase running pid=$(cat "${PIDFILE}") state=$(cat "${STATE}" 2>/dev/null || echo UNKNOWN)"
            exit 0
        fi
        "${FACTORY}" status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}" >&2
        exit 1
        ;;
esac

exit 0

#!/bin/sh
set -u

DISABLE=${WORLD_PL_DISABLE:-/boot/world_pl/DISABLE}
SERVICE=${WORLD_PL_SERVICE:-/etc/init.d/world-voice}

case "${1:-}" in
    enable)
        rm -f "${DISABLE}"
        sync
        "${SERVICE}" restart
        ;;
    disable)
        mkdir -p "$(dirname "${DISABLE}")"
        printf '%s\n' MANUAL > "${DISABLE}"
        sync
        "${SERVICE}" restart
        ;;
    status)
        if [ -e "${DISABLE}" ]; then
            echo "boot selection: factory v23 (DISABLE present: $(cat "${DISABLE}" 2>/dev/null))"
        else
            echo "boot selection: WORLD minphase PL candidate"
        fi
        "${SERVICE}" status
        ;;
    *)
        echo "Usage: world-pl-control {enable|disable|status}" >&2
        exit 1
        ;;
esac

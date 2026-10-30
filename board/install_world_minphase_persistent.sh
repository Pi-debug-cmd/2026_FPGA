#!/bin/sh
# Install persistent assets without starting candidate FPGA or audio.
set -eu

STAGE=${1:?usage: install_world_minphase_persistent.sh STAGE_DIR}
RELEASE=/opt/world_voice_pl/releases/20261029_round27
APP_ROOT=/opt/world_voice_pl
BOOT_DIR=/boot/world_pl
INIT=/etc/init.d/world-voice
FACTORY_INIT=/etc/init.d/world-voice.factory
CONTROL=/usr/sbin/world-pl-control

expect_sha() {
    expected=$1
    path=$2
    actual=$(sha256sum "${path}" | awk '{print $1}')
    [ "${actual}" = "${expected}" ] || {
        echo "SHA mismatch: ${path}: ${actual} != ${expected}" >&2
        exit 1
    }
}

# Refuse installation if any factory baseline changed.
expect_sha 067ba4d216fcdef094673e1e02da7b2ddbbd705c41553ac0b3a93d4259dd2447 "${INIT}"
expect_sha 16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61 /boot/bit/zynq7020.bit
expect_sha e211c7f8b8034c02c9035d71c05237607f09efeec272ad9d9c774788431c53c2 /boot/uEnv.txt
expect_sha 7702e40c863bb4d73b561ad9dd112537fd4560515286e9a3f5aebb133a6383f8 /boot/boot.scr
expect_sha f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7 /opt/world_voice/world_budget_v23
test ! -e "${FACTORY_INIT}"
test ! -e "${RELEASE}"
test ! -e "${BOOT_DIR}"

expect_sha 7715bd0138922ca1f2c34a7ac0cd7d889ce26539dde101824323051be3c5d1a0 "${STAGE}/rootfs/manifest.sha256"
(cd "${STAGE}/rootfs" && sha256sum -c manifest.sha256)
expect_sha 211392ced7800c5e09db0a9cb8dade1cfe39da939faf3ce1a56e414e795bc499 "${STAGE}/install/world_minphase_init.sh"
expect_sha a097d330aaee63f49f602d38300bd964ca04514310e0e2f96589acad77d89dd6 "${STAGE}/install/world_minphase_control.sh"
expect_sha 5e1ec6b17074f4a831ff47803723adb602053153efb30123d50949784e9be322 "${STAGE}/boot/manifest.sha256"
expect_sha 6c015fefebdb784c473f009ddd26ba7704d614b6918d0032b0fdf2bda5cabbc2 "${STAGE}/boot/recovery.json"
(cd "${STAGE}/boot" && sha256sum -c manifest.sha256)

# Rootfs release is versioned; current is a symlink, so rollback is explicit.
mkdir -p "${APP_ROOT}/releases"
mkdir "${RELEASE}"
cp "${STAGE}/rootfs/"* "${RELEASE}/"
chmod 0755 "${RELEASE}/world_minphase_autostart.sh" \
    "${RELEASE}/world_exp_switch.py" "${RELEASE}/live_world_trial.py" \
    "${RELEASE}/world_budget_v24"
chmod 0644 "${RELEASE}/world_minphase_dma.ko" \
    "${RELEASE}/world_live_manifest_v21.json" "${RELEASE}/manifest.sha256"
(cd "${RELEASE}" && sha256sum -c manifest.sha256)
ln -s "${RELEASE}" "${APP_ROOT}/current.new"
mv "${APP_ROOT}/current.new" "${APP_ROOT}/current"

# Preserve the exact factory init before atomically replacing its entry point.
cp -p "${INIT}" "${FACTORY_INIT}.new"
expect_sha 067ba4d216fcdef094673e1e02da7b2ddbbd705c41553ac0b3a93d4259dd2447 "${FACTORY_INIT}.new"
mv "${FACTORY_INIT}.new" "${FACTORY_INIT}"
cp "${STAGE}/install/world_minphase_init.sh" "${INIT}.new"
chmod 0755 "${INIT}.new"
mv "${INIT}.new" "${INIT}"
cp "${STAGE}/install/world_minphase_control.sh" "${CONTROL}.new"
chmod 0755 "${CONTROL}.new"
mv "${CONTROL}.new" "${CONTROL}"

# INSTALL_GUARD makes this write non-activating. Original boot files stay untouched.
mkdir "${BOOT_DIR}"
printf '%s\n' INSTALL_GUARD > "${BOOT_DIR}/DISABLE"
cp "${STAGE}/boot/world_minphase_swap.bin.gz" "${BOOT_DIR}/world_minphase_swap.bin.gz"
cp "${STAGE}/boot/manifest.sha256" "${BOOT_DIR}/manifest.sha256"
cp "${STAGE}/boot/recovery.json" "${BOOT_DIR}/recovery.json"
sync
(cd "${BOOT_DIR}" && sha256sum -c manifest.sha256)

# Final readback includes all factory files and installed selectors.
expect_sha 067ba4d216fcdef094673e1e02da7b2ddbbd705c41553ac0b3a93d4259dd2447 "${FACTORY_INIT}"
expect_sha 211392ced7800c5e09db0a9cb8dade1cfe39da939faf3ce1a56e414e795bc499 "${INIT}"
expect_sha a097d330aaee63f49f602d38300bd964ca04514310e0e2f96589acad77d89dd6 "${CONTROL}"
expect_sha 16cb36f7161935896615ad12b000597088a6a9745856611162f1c44a51f82a61 /boot/bit/zynq7020.bit
expect_sha e211c7f8b8034c02c9035d71c05237607f09efeec272ad9d9c774788431c53c2 /boot/uEnv.txt
expect_sha 7702e40c863bb4d73b561ad9dd112537fd4560515286e9a3f5aebb133a6383f8 /boot/boot.scr
expect_sha f12da25e93a520b7f5255ce952a3cb9b5d1bbca474133b1bc529d8c8e18349b7 /opt/world_voice/world_budget_v23
[ "$(cat "${BOOT_DIR}/DISABLE")" = INSTALL_GUARD ]

echo 'WORLD_MINPHASE_INSTALL_OK active=factory guard=INSTALL_GUARD boot_originals_unchanged=1'

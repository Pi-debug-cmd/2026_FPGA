# SD Card Backup and Inventory - 2026-11-02

## Device and backup

- USB disk: `Generic STORAGE DEVICE`, Windows Disk 1, 15,978,201,088 bytes.
- Partition 1: MBR type 0x0c FAT32, 41,943,040 bytes, mounted as `E:`.
- Partition 2: MBR type 0x83 Linux, 15,934,160,896 bytes, not readable through the Windows volume mount.
- Destination: `D:\2026_FPGA_sd_boot_files_20261102` (D: had about 77.5 GB free before imaging).
- A raw read-only image was started at `D:\2026_FPGA_sd_backup_20261102.img`. Physical-disk reads stopped with Windows CRC error at approximately byte offset 11,811,160,064. The resulting file is partial and must not be treated as a valid image. Its last observed size was 11,844,714,496 bytes; no whole-image hash was produced.
- Recovery was not completed. Do not use the partial raw image to restore a card. Retry with a reliable reader/card or a recovery imager that logs unreadable sectors; preserve the source card unchanged.

## FAT32 files copied

The backup folder contains 35 files totaling 21,473,587 bytes. Each copied file was SHA-256 checked against the mounted source and matched. The folder includes `SD卡.zip` (7,030,886 bytes); its archive entries match the boot files and FAT32 tree, so it is not a full-card image.

Key files observed on the card:

- `BOOT.BIN`, 1,101,624 bytes, SHA-256 `F0E985E6CE91C8205EC30F0D66C19273CAE0E92DEF9D41DEDC0DBB5812EFED75`.
- `boot.scr`, 1,982 bytes, SHA-256 `7702E40C863BB4D73B561AD9DD112537FD4560515286E9A3F5AEBB133A6383F8`.
- `uEnv.txt`, 1,077 bytes, SHA-256 `E211C7F8B8034C02C9035D71C05237607F09EFEEC272AD9D9C774788431C53C2`.
- `kernel/zImage`, 4,503,288 bytes, SHA-256 `311D2C1FA8448724DF9D14C6493D08EF96E825B60E785A087FC81C52C128D98F`.
- `bit/zynq7020.bit`, 4,045,672 bytes, SHA-256 `16CB36F7161935896615AD12B000597088A6A9745856611162F1C44A51F82A61`.
- `world_pl/world_minphase_swap.bin.gz`, 536,768 bytes, SHA-256 `6A7FEC9987D31C5F803B79B1BB8E115DCA9FDA0DFC278B8F462D60562B628D98`.

`boot.scr` loads `kernel/zImage`, the Zynq-7020 DTB, and the bitstream from partition 1, then boots with the root filesystem on partition 2. No `image.ub` or standalone PetaLinux image was found in the FAT32 partition. The card does contain usable boot components, a Zynq-7020 bitstream, and a `world_pl` runtime payload; these are not the project's Vivado source or a PetaLinux build image.

## Linux partition status

Partition 2 was not inspected because Windows exposes no filesystem volume for it and whole-disk imaging failed on a read CRC error. Presence of project files, a PetaLinux root filesystem, or a reusable image inside that partition remains unknown. The boot script indicates that partition 2 is expected to provide the root filesystem, but does not establish that it contains a complete PetaLinux project or build output.

## Reproduction

```powershell
Get-Disk
Get-Partition -DiskNumber 1
Get-ChildItem E:\ -Force -Recurse
Get-FileHash -Algorithm SHA256 E:\BOOT.BIN,E:\boot.scr,E:\uEnv.txt,E:\SD卡.zip
```

The original card was not intentionally written to. Do not restore the partial image. Next step: retry with another reader/adapter or recovery imager and inspect partition 2 read-only after a verifiable full backup is obtained.

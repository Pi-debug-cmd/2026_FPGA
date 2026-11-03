# SD Card Recovery and Inventory - 2026-11-03

## Device and image

- Source: USB disk `Generic STORAGE DEVICE`, Windows Disk 1, 15,978,201,088 bytes; MBR partition 1 is FAT32 (41,943,040 bytes), partition 2 is Linux (15,934,160,896 bytes).
- Full-capacity raw image: `D:\2026_FPGA_sd_backup_20261102.img`, 15,978,201,088 bytes. SHA-256: `8A55C0136215FB1DF337370281F1A3F5B6AA79800B7C19F21DE7D60196E90AD3`.
- Read log: `D:\2026_FPGA_sd_backup_status.txt`; it ends with `TAIL_COMPLETE bytes=15978201088` at 2026-11-03 00:10:44 UTC. The full image hash was independently recomputed after capture.
- The recovery log records 30 failed 512-byte sectors (15,360 bytes) and 16 failed tail ranges (1,033,728 bytes). Those 1,049,088 bytes were zero-filled after three CRC retries per range. Thus the image covers the whole device but is not a lossless copy; do not describe it as an error-free backup or use it as a known-good restoration source. Preserve the original SD card unchanged.
- The initial CRC at byte offset 11,811,160,064 was transient: adjacent sector probes and 512 KiB, 1 MiB, and 8 MiB reads later passed, and the adaptive reread crossed it. The remaining repeatable CRC failures were concentrated near the device end.
- A post-capture retry confirmed Disk 1 remains online and marked read-only, but the current process was denied a read handle to `\\.\PhysicalDrive1`; no source read or image patch occurred during that retry. The original acquisition log's CRC failures therefore remain unresolved at the byte level.
- Separate FAT32 file copy: `D:\2026_FPGA_sd_boot_files_20261102`, 35 files totaling 21,473,587 bytes; each copied file's SHA-256 matched the mounted source.

## Inventory

- FAT32 includes `BOOT.BIN`, `boot.scr`, `uEnv.txt`, `kernel/zImage`, Zynq-7020 device tree and bitstream, and `world_pl` runtime files. No standalone `image.ub`, `.img`, or `.wic` image was found on the boot partition.
- The Linux partition is ext4, labeled `ROOTFS`. It contains a bootable PetaLinux root filesystem and runtime project assets under `/opt/world_voice` and `/opt/world_voice_pl/releases/20261029_round27` and `20261030_round30`, including `world_budget_v23/v24`, DMA modules, scripts, and manifests.
- No Vivado `.xpr`, `.xsa`, `.hdf`, or PetaLinux `project-spec` source tree was found. The card therefore provides a bootable system and runtime assets, but not the complete rebuildable Vivado/PetaLinux project or a separate PetaLinux build image.
- `/etc/petalinux/version` reports `1.00`; this is not sufficient evidence of the PetaLinux toolchain version. Existing project records identify the previously used board environment as PetaLinux 2022.2, but the card's version file alone does not confirm it.

## Reproduction and limits

```powershell
(Get-Item D:\2026_FPGA_sd_backup_20261102.img).Length
Get-FileHash D:\2026_FPGA_sd_backup_20261102.img -Algorithm SHA256
Select-String '^BAD_SECTOR|^BAD_RANGE|^TAIL_COMPLETE' D:\2026_FPGA_sd_backup_status.txt
```

The SD card was not intentionally written to. The image itself and raw acquisition log remain outside Git because they are large generated evidence. The FAT32 copy is also local. This is a recovered full-length image with documented unreadable regions, not a lossless image. The image and read log should be kept together. To recover the zero-filled bytes, retry in a process with raw-disk read access or with a different reader/adapter and recovery imager; do not overwrite the source card.

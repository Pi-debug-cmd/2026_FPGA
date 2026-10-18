"""Read-only snapshot of active audio/DMA device-tree resources."""
import json
from pathlib import Path
import struct

root = Path('/sys/firmware/devicetree/base')
nodes = []
for prop in root.rglob('compatible'):
    compatible = prop.read_bytes().rstrip(b'\0').decode(errors='replace').split('\0')
    if prop.parent.relative_to(root).parts[:1] != ('amba_pl',) and not any(any(word in item for word in ('audio', 'i2s', 'dynclk', 'axi-dma', 'wm8960', 'gemm')) for item in compatible):
        continue
    node = {'path': str(prop.parent.relative_to(root)), 'compatible': compatible}
    for name in ('reg', 'interrupts', 'interrupt-parent', 'clocks'):
        file = prop.parent / name
        if file.exists():
            raw = file.read_bytes()
            node[name + '_u32'] = list(struct.unpack('>' + 'I' * (len(raw)//4), raw))
    status = prop.parent / 'status'
    node['status'] = status.read_bytes().rstrip(b'\0').decode() if status.exists() else 'okay (implicit)'
    nodes.append(node)
snapshot = {'device_tree_nodes': nodes, 'iomem': Path('/proc/iomem').read_text(), 'interrupts': Path('/proc/interrupts').read_text()}
print(json.dumps(snapshot, indent=2))

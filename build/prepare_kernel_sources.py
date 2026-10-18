"""Extract the supplied kernel archive after checking paths and all link chains."""
import collections
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

archive, destination, config, manifest = map(Path, sys.argv[1:])
destination.mkdir(parents=True, exist_ok=False)
with tarfile.open(str(archive), 'r:gz') as package:
    members = package.getmembers()
    prefix = PurePosixPath(members[0].name).parts[0]
    links = {m.name.rstrip('/'): m.linkname for m in members if m.issym()}

    def resolve(parts):
        queue, stack, hops = collections.deque(parts), [], 0
        while queue:
            item = queue.popleft()
            if item in ('', '.'):
                continue
            if item == '..':
                if len(stack) <= 1:
                    raise ValueError('Link escapes archive root')
                stack.pop()
                continue
            stack.append(item)
            target = links.get('/'.join(stack))
            if target is not None:
                if PurePosixPath(target).is_absolute():
                    raise ValueError('Absolute symlink')
                stack.pop()
                queue.extendleft(reversed(PurePosixPath(target).parts))
                hops += 1
                if hops > 40:
                    raise ValueError('Cyclic link')
        if not stack or stack[0] != prefix:
            raise ValueError('Path escapes archive root')

    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or path.parts[0] != prefix:
            raise ValueError('Unsafe archive member: ' + member.name)
        if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
            raise ValueError('Unsupported archive file type')
        resolve(path.parts)
        if member.islnk():
            target = PurePosixPath(member.linkname)
            if target.is_absolute():
                raise ValueError('Absolute hardlink')
            resolve(target.parts)
    package.extractall(str(destination), members=members)
source = destination / prefix
record = {'source': str(source), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
          'config_gz_sha256': hashlib.sha256(config.read_bytes()).hexdigest(), 'archive_members': len(members)}
Path(manifest).write_text(json.dumps(record, indent=2) + '\n')
print(source)

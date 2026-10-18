"""Collect the installed ASR runtime and its ELF dependencies, not the toolkit."""
import os
from pathlib import Path
import re
import shutil
import subprocess

root = Path('/runtime')
prefix = root / 'opt/nemo'
(prefix / 'bin').mkdir(parents=True)
(prefix / 'lib').mkdir()
shutil.copy2('/opt/nemo/bin/nemo-speech', prefix / 'bin/nemo-speech')
shutil.copytree('/opt/nemo/share/licenses', prefix / 'share/licenses')
for name in ('LICENSE', 'NOTICE', 'THIRD_PARTY_NOTICES.md'):
    shutil.copy2('/src/' + name, prefix / 'share/licenses/nemo-speech' / name)
notices = prefix / 'share/licenses/runtime'
notices.mkdir()
for path in [Path('/usr/local/cuda/EULA.txt'), Path('/NGC-DL-CONTAINER-LICENSE'),
             *Path('/usr/share/doc').glob('libgomp*/copyright'),
             *Path('/usr/share/doc').glob('libsentencepiece*/copyright'),
             *Path('/usr/share/doc').glob('libcublas*/copyright'),
             *Path('/usr/share/doc').glob('cuda-cudart*/copyright')]:
    if path.is_file():
        shutil.copy2(path, notices / f'{path.parent.name}-{path.name}')

# cc-debian13 supplies glibc, libstdc++, and libgcc. Never transplant Ubuntu's
# loader/libc into Distroless; all other transitive libraries are collected.
base = re.compile(r'^(ld-linux.*|lib(c|m|dl|pthread|rt|resolv|util)\.so\..*|libstdc\+\+\.so\..*|libgcc_s\.so\..*)$')
env = dict(os.environ, LD_LIBRARY_PATH='/opt/nemo/lib:/usr/local/cuda/lib64')
pending = [Path('/opt/nemo/bin/nemo-speech'), *Path('/opt/nemo/lib').glob('*.so*')]
seen = set()
while pending:
    binary = pending.pop()
    if binary.resolve() in seen:
        continue
    seen.add(binary.resolve())
    if binary.name != 'nemo-speech':
        shutil.copy2(binary.resolve(), prefix / 'lib' / binary.name)
    result = subprocess.run(['ldd', str(binary)], env=env, text=True, capture_output=True, check=True)
    for line in result.stdout.splitlines():
        if 'not found' in line:
            if line.strip().startswith('libcuda.so.1 '):
                continue  # Injected by the host, NEVER ship the driver/stub.
            raise RuntimeError(f'Unresolved dependency: {line}')
        match = re.search(r'=> (/\S+)', line)
        if match and not base.match(Path(match[1]).name):
            pending.append(Path(match[1]))

stub = next(Path('/usr/local/cuda/targets').glob('*/lib/stubs/libcuda.so'))
Path('/driver-stub').mkdir()
shutil.copy2(stub, '/driver-stub/libcuda.so.1')
home = root / 'home/asr'
home.mkdir(parents=True)
os.chown(home, 1000, 1000)

"""Build-time packaging assertions; no GPU or weights required."""
from pathlib import Path

root = Path('/runtime')
assert (root / 'opt/nemo/bin/nemo-speech').is_file()
libs = [p.name for p in (root / 'opt/nemo/lib').iterdir()]
assert any('ggml-cuda' in name for name in libs), libs
assert any('cublas' in name for name in libs), libs
assert not any(name.startswith('libcuda.so') for name in libs), libs
assert (root / 'home/asr').stat().st_uid == 1000
assert (root / 'opt/nemo/share/licenses/nemo-speech/NOTICE').is_file()
assert not list(root.rglob('*.gguf'))
for forbidden in ('bin/sh', 'bin/bash', 'usr/bin/apt', 'usr/bin/gcc', 'usr/local/cuda/bin/nvcc'):
    assert not (root / forbidden).exists(), forbidden
print('Runtime packaging checks passed')

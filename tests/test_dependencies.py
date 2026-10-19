"""Ensure local and CI builds consume the Dependabot-managed source tree."""
import configparser
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'upstream/NeMo-Speech.cpp'


class SourceDependencies(unittest.TestCase):
    def test_submodule_manifest(self):
        manifest = configparser.ConfigParser()
        manifest.read(ROOT / '.gitmodules')
        dependency = manifest['submodule "upstream/NeMo-Speech.cpp"']
        self.assertEqual(dependency['path'], 'upstream/NeMo-Speech.cpp')
        self.assertEqual(dependency['url'], 'https://github.com/NVIDIA/NeMo-Speech.cpp.git')

    def test_required_sources_present(self):
        for name in ('CMakeLists.txt', 'patches/series', 'llama.cpp/ggml/CMakeLists.txt',
                     'third_party/cpp-httplib/httplib.h'):
            with self.subTest(path=name):
                self.assertTrue((SOURCE / name).is_file(), f'Initialize submodules: missing {name}')

    def test_checkout_matches_recorded_revision(self):
        # Check nested gitlinks too: updating the root dependency must not
        # independently float its ggml/HTTP dependencies to unrelated heads.
        for directory, paths in [(ROOT, ['upstream/NeMo-Speech.cpp']),
                                 (SOURCE, ['llama.cpp', 'third_party/cpp-httplib'])]:
            status = subprocess.check_output(['git', '-C', str(directory), 'submodule',
                                              'status', '--', *paths], text=True)
            for line in status.splitlines():
                self.assertTrue(line.startswith(' '), f'Submodule checkout mismatch: {line}')

    def test_dockerfile_uses_checkout_not_hidden_revision(self):
        dockerfile = (ROOT / 'Dockerfile').read_text()
        self.assertIn('COPY upstream/NeMo-Speech.cpp /src', dockerfile)
        self.assertNotIn('NEMO_SPEECH_REF', dockerfile)
        self.assertNotIn('git fetch', dockerfile)


if __name__ == '__main__':
    unittest.main()

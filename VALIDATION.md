# Validation

Initial implementation: 2026-10-18.

Passed locally:
- Python and workflow YAML syntax checks.
- Four timestamp-validator unit tests (including rejection of missing,
  non-finite, reversed, out-of-range and out-of-order timestamps).
- Deployment config validated against upstream llama-swap's JSON schema;
  existing model definitions and matrix sets are unchanged. Parakeet is alone
  in the new `asr` set. The live config hot-reload and model listing passed.
- Official NVIDIA GGUF downloaded separately and SHA256 verified:
  `e3880d0aaaaf2c308ea2c35016b2b895c423eb3fda924c1b463d1c19b7f4d32e`.

The first CI attempt exposed a missing SentencePiece development dependency at
CMake configure time; the builder now explicitly installs it. NCCL is disabled
because this image serves a single ASR model on one GPU.

## Published ARM64 image and GB10 end-to-end test

On 2026-10-18 UTC, the ARM64 job of
[run 39175731583](https://github.com/UnitVectorY-Labs/docker-parakeet-tdt/actions/runs/39175731583)
passed packaging assertions and all three help checks in the actual Distroless
runtime, then published source `176360af9fe1bef47e50893c6e509a19cfab8baa`:

- ARM64 OCI index: `sha256:5ef92912275367f0783f54a4f208d810b3979b683b491aa5a6056664467729f8`
- ARM64 platform manifest: `sha256:8270045c982848de8b5784e1eb71bad3cabf882db6b6be9e0230eafcbee7b74d`
- Running image config ID: `sha256:8c85f5705a7be7974a3fb71f2a293f9141ba6aef8bc031e0413fc0721100ce50`

The deployment pulled and pinned this published digest with `--pull always`;
no local image build was used. On NVIDIA GB10 with driver **580.178.04**:

- Ran as UID/GID 1000 with the external official Q8_0 GGUF mounted read-only.
- Startup reported `head=tdt backend=CUDA0`.
- `tests/transcribe.py` sent the upstream 11-second JFK WAV through the live
  HTTPS llama-swap `/v1/audio/transcriptions` route. HTTP 200; transcript:
  “And so, my fellow Americans, ask not what your country can do for you, ask
  what you can do for your country.”
- **22 words** with finite, ordered start/end times passed all assertions.
  First word: `And`, 0.24–0.56 seconds. Response duration: 11 seconds.
- Native CLI readiness check against `/ready` passed.
- llama-swap unload returned HTTP 200 and removed the container. Physical
  available memory returned from ~116 GiB after inference to ~117 GiB after
  unload (~118 GiB before startup). These snapshots are not peak measurements.
- No other model was running or interrupted; no Compose restart was performed.

Raw evidence lives on the test host at `/tmp/opencode/parakeet-jfk-timestamped.json`
and `/tmp/opencode/parakeet-gpu.log`, not in Git.

Both architecture jobs and the manifest job subsequently completed successfully
in run 39175731583. The published multi-platform index was
`sha256:9ff32d13e61d56ee7cfe293619d6176eec8ec5132213e47e96d012eef59898f7`;
its ARM64 platform manifest is the same one tested above.

AMD64 GPU inference, long recordings, dataset-level timestamp accuracy, TTL
expiry, Docker's periodic health transition, and LLM/TTS co-loading remain
unverified. Successful AMD64 CPU/build checks do not establish AMD64 GPU inference.

## Merged CUDA update and dependency maintenance (2026-10-19)

PR #1 (CUDA 13.0.2 → 13.4.2) was merged by the repository owner on
2026-10-19. It is unrelated to the earlier missing-SentencePiece failure.
The implementation and README now use that merged main as their base.
R580 supports CUDA 13.x minor-version compatibility with PTX/new-feature
limitations; GPU-less build checks cannot establish actual new CUDA/cuBLAS
compatibility. The successful GPU test above remains evidence for the old
CUDA 13.0.2 artifact only, not the CUDA 13.4.2 image.

NeMo-Speech.cpp now uses a Dependabot-managed Git submodule rather than a
Dockerfile SHA ARG. The initial recorded revision remains the previously
tested `caa3f47c7c75fa2e9e6340272ebad57c1647dd44`; this packaging change does
not silently upgrade upstream code. CI initializes and tests the recorded
source and its required nested dependencies. Docker and Actions dependencies
retain their existing Dependabot coverage. There are no pip dependencies
to track in `requirements.txt`.

Local validation of this maintenance change passed **8 unit tests** (four
dependency-checkout checks and four timestamp-validation checks), Python/YAML
syntax, Dependabot ecosystem coverage, CI submodule path filters, and
`git diff --check`. No local image build was performed; the new CUDA 13.4.2
image must pass GitHub CI and separate GPU validation before replacing the
previously tested deployment digest.

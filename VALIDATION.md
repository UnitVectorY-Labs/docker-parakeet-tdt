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

AMD64 GPU inference, long recordings, dataset-level timestamp accuracy, TTL
expiry, Docker's periodic health transition, and LLM/TTS co-loading remain
unverified. ARM64 validation does not establish the status of the separate
AMD64 build or multi-platform tag publication.

## CUDA version-bump PR

PR #1 proposes CUDA 13.0.2 → 13.4.2; it is unrelated to the missing
SentencePiece failure. It was not merged. R580 supports CUDA 13.x minor-version
compatibility with PTX/new-feature limitations; GPU-less build checks cannot
establish actual new CUDA/cuBLAS compatibility. Rebase onto the fixed main and
validate on GB10 separately before adopting the bump, including updating the
README's version references.

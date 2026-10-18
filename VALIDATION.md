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

GPU inference and published-image results will be recorded here only after
they have actually completed. CPU packaging/help checks and the provided
end-to-end test are distinct; publication alone does not establish successful
transcription. AMD64 GPU inference, long recordings, timestamp accuracy and
LLM/TTS co-loading are not validated by the local checks above.

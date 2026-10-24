# syntax=docker/dockerfile:1
FROM nvidia/cuda:13.4.3-devel-ubuntu24.04 AS builder
# Portable native builds: no build-host CPU/GPU autodetection. Includes GB10 sm_121.
ARG CUDA_ARCHITECTURES="80;86;89;90;100;120;121"
ARG BUILD_JOBS=2
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates git cmake ninja-build g++ python3 libgomp1 pkg-config libsentencepiece-dev \
    && rm -rf /var/lib/apt/lists/*
# The source revision is a Dependabot-managed Git submodule, not a Docker ARG.
# Initialize its required nested submodules before building (see README).
COPY upstream/NeMo-Speech.cpp /src
RUN test -f /src/llama.cpp/ggml/CMakeLists.txt \
    && test -f /src/third_party/cpp-httplib/httplib.h
RUN cmake -S /src -B /build -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/opt/nemo \
    -DCMAKE_INSTALL_LIBDIR=lib -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHITECTURES}" \
    -DGGML_CUDA=ON -DGGML_NATIVE=OFF -DGGML_BACKEND_DL=OFF -DGGML_CUDA_NCCL=OFF \
    -DNEMO_SPEECH_BUILD_ASR=ON -DNEMO_SPEECH_BUILD_HTTP=ON \
    -DNEMO_SPEECH_BUILD_DIAR=OFF -DNEMO_SPEECH_BUILD_TTS=OFF \
    -DNEMO_SPEECH_BUILD_NMT=OFF -DNEMO_SPEECH_BUILD_S2S=OFF \
    -DNEMO_SPEECH_BUILD_MIC_CAPTURE=OFF -DNEMO_SPEECH_BUILD_GRPC=OFF \
    -DNEMO_SPEECH_BUILD_TESTS=OFF -DNEMO_SPEECH_HTTP_TLS=OFF \
    && cmake --build /build --parallel "${BUILD_JOBS}" \
    && cmake --install /build
COPY assemble_runtime.py /assemble_runtime.py
RUN python3 /assemble_runtime.py
COPY tests/test_image.py /test_image.py
RUN python3 /test_image.py

FROM gcr.io/distroless/cc-debian13:nonroot AS runtime
ENV LD_LIBRARY_PATH=/opt/nemo/lib \
    HOME=/home/asr \
    NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility
COPY --from=builder /runtime/ /
WORKDIR /opt/nemo
USER 1000:1000
EXPOSE 8080
ENTRYPOINT ["/opt/nemo/bin/nemo-speech"]
CMD ["serve", "--asr-model", "/model/parakeet-tdt-0.6b-v3.q8_0.gguf", "--gpu", "0", "--host", "0.0.0.0", "--port", "8080", "--no-ui", "--threads", "1", "--max-upload-mb", "32"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=5m --retries=3 \
    CMD ["/opt/nemo/bin/nemo-speech", "health", "--url", "http://127.0.0.1:8080/ready", "--timeout", "2", "--quiet"]

# CI has no GPU. Link against the toolkit's driver stub ONLY in this test stage.
# The final runtime must obtain the real driver from NVIDIA Container Toolkit.
FROM runtime AS validated
COPY --from=builder /driver-stub/libcuda.so.1 /opt/nemo/lib/libcuda.so.1
RUN ["/opt/nemo/bin/nemo-speech", "--help"]
RUN ["/opt/nemo/bin/nemo-speech", "serve", "--help"]
RUN ["/opt/nemo/bin/nemo-speech", "health", "--help"]

FROM runtime AS final
# This dependency forces execution of the shell-free runtime checks above.
COPY --from=validated /opt/nemo/share/licenses/nemo-speech/LICENSE /opt/cpu-tests-passed

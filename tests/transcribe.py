#!/usr/bin/env python3
"""End-to-end WAV transcription with word timestamps (stdlib only)."""
import argparse
import json
import math
from pathlib import Path
import uuid
import urllib.request


def validate(result):
    assert isinstance(result['text'], str) and result['text'].strip(), result
    assert result['task'] == 'transcribe', result
    duration = result['duration']
    assert isinstance(duration, (int, float)) and math.isfinite(duration) and duration > 0
    assert isinstance(result['words'], list) and result['words'], result
    previous = -1.0
    for word in result['words']:
        assert isinstance(word['word'], str) and word['word'].strip(), word
        start, end = word['start'], word['end']
        assert all(isinstance(t, (int, float)) and math.isfinite(t) for t in (start, end)), word
        assert 0 <= start <= end <= duration + 0.5, word
        assert start >= previous, word
        previous = start


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('audio', type=Path, help='short WAV file containing speech')
    parser.add_argument('--base-url', default='http://127.0.0.1:8080')
    parser.add_argument('--model', default='parakeet-tdt-0.6b-v3')
    args = parser.parse_args()
    boundary = uuid.uuid4().hex
    body = bytearray()
    for key, value in {'model': args.model, 'response_format': 'verbose_json'}.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="audio.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode())
    body.extend(args.audio.read_bytes())
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    request = urllib.request.Request(args.base_url.rstrip('/') + '/v1/audio/transcriptions', data=bytes(body),
                                     headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    with urllib.request.urlopen(request, timeout=900) as response:
        result = json.load(response)
    validate(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
CACHE="$ROOT/.engine-cache"
RUNTIME="$ROOT/.engine-runtime"
TAG="${ENGINE_RELEASE_TAG:-ai-engine-v1}"
mkdir -p "$CACHE" "$RUNTIME"
if [[ ! -f "$CACHE/engine-manifest.json" ]]; then
  gh release download "$TAG" --repo "$GITHUB_REPOSITORY" --dir "$CACHE" \
    --pattern "engine-manifest.json" \
    --pattern "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" \
    --pattern "llama-cpp-ubuntu-x64.tar.gz"
fi
python3 - "$CACHE" <<'PY2'
import hashlib, json, sys
from pathlib import Path
root = Path(sys.argv[1])
manifest = json.loads((root / 'engine-manifest.json').read_text(encoding='utf-8'))
for asset in manifest['assets']:
    path = root / asset['name']
    if not path.is_file():
        raise SystemExit(f'Missing asset: {path}')
    if hashlib.sha256(path.read_bytes()).hexdigest() != asset['sha256']:
        raise SystemExit(f'SHA256 mismatch: {path.name}')
print('Engine assets verified.')
PY2
rm -rf "$RUNTIME/llama"
mkdir -p "$RUNTIME/llama"
tar -xzf "$CACHE/llama-cpp-ubuntu-x64.tar.gz" -C "$RUNTIME/llama"
SERVER="$(find "$RUNTIME/llama" -type f -name llama-server | head -n 1)"
test -n "$SERVER"
chmod +x "$SERVER"
printf '%s\n' "$SERVER" > "$RUNTIME/server-path.txt"
printf '%s\n' "$CACHE/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf" > "$RUNTIME/model-path.txt"

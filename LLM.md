# Local LLM

Recommended Windows runtime: current CUDA build of [`llama.cpp`](https://github.com/ggml-org/llama.cpp) `llama-server`, bound to `127.0.0.1`. It supports the V100, OpenAI-compatible chat completions and JSON-schema-constrained output without another desktop application. The default model family is [`Qwen/Qwen3-8B`](https://huggingface.co/Qwen/Qwen3-8B) (Apache-2.0, 100+ languages) in GGUF Q4_K_M. A quantized conversion is a separate artifact: verify its publisher, license, revision and SHA-256; weights are never committed.

Suggested command:

```powershell
llama-server.exe -m C:\models\Qwen3-8B-Q4_K_M.gguf -ngl 99 -c 4096 --host 127.0.0.1 --port 8080
```

Start conservatively with one request slot, no speculative decoding, a 4k context, and observe `nvidia-smi`. The application sends temperature `0.1`, seed `42`, `/no_think`, and `response_format=json_schema`; it retries once and stores model/prompt identity. `LLM_BASE_URL` and `LLM_MODEL` replace the backend without changing business logic. The offline rules classifier exists only for tests and smoke checks, not production classification.

WSL2/Linux remains portable but is not the primary path because WSL enumeration was unavailable during the initial Windows audit. On a future Linux/VM host, use the official CUDA `llama.cpp` server image or native binary and keep the endpoint private.

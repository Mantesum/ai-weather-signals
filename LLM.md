# Local LLM

Recommended Windows runtime is Ollama bound to `127.0.0.1`. This deployment uses `qwen3.5:9b`, which fits the audited V100 16 GB and provides stronger multilingual extraction than the smaller 4B fallback. The native Ollama API receives the full JSON schema and `think: false`, avoiding hidden reasoning latency. Configure it with:

```dotenv
LLM_PROVIDER=ollama
LLM_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=qwen3.5:9b
LLM_TIMEOUT_SECONDS=60
```

`llama.cpp` remains supported through the OpenAI-compatible provider:

Suggested command:

```powershell
llama-server.exe -m C:\models\Qwen3-8B-Q4_K_M.gguf -ngl 99 -c 4096 --host 127.0.0.1 --port 8080
```

Set `LLM_PROVIDER=openai` and use the `/v1` base URL for llama.cpp or another compatible server. The application sends temperature `0.1`, seed `42`, constrained JSON, retries once, and stores model/prompt identity. `weather-signals collect --max-runtime-seconds N` safely bounds a collection run; a partial run does not advance the source cursor. The offline rules classifier exists only for tests and smoke checks, not production classification.

WSL2/Linux remains portable but is not the primary path because WSL enumeration was unavailable during the initial Windows audit. On a future Linux/VM host, use the official CUDA `llama.cpp` server image or native binary and keep the endpoint private.

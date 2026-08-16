# Local LLM

Recommended Windows runtime is Ollama bound to `127.0.0.1`. This deployment uses `qwen3.5:9b`, which fits the audited V100 16 GB and provides stronger multilingual extraction than the smaller 4B fallback. The native Ollama API receives the full JSON schema and `think: false`, avoiding hidden reasoning latency. Configure it with:

```dotenv
LLM_PROVIDER=ollama
LLM_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=qwen3.5:9b
LLM_TIMEOUT_SECONDS=45
LLM_MAX_INPUT_CHARS=2000
```

Ollama requests keep the model loaded for 15 minutes, cap input at 2,000 characters and generation at
160 tokens. A timed-out request is not repeated; invalid structured output may be retried once.

On the audited Tesla V100 Windows host, Ollama's default CUDA 13 runner omits compute capability 7.0.
Forcing its bundled CUDA 12 runner loaded the model into VRAM but caused a driver-level GPU loss, so the
deployment remains in automatic CPU mode until Windows is rebooted and a stable sm_70-capable runtime is
validated. Do not force `OLLAMA_LLM_LIBRARY` on that host without a recovery window.

`llama.cpp` remains supported through the OpenAI-compatible provider:

Suggested command:

```powershell
llama-server.exe -m C:\models\Qwen3-8B-Q4_K_M.gguf -ngl 99 -c 4096 --host 127.0.0.1 --port 8080
```

Set `LLM_PROVIDER=openai` and use the `/v1` base URL for llama.cpp or another compatible server. The application sends temperature `0.1`, seed `42`, constrained JSON, retries once, and stores model/prompt identity. `weather-signals collect --max-runtime-seconds N` safely bounds a collection run; a partial run does not advance the source cursor. The offline rules classifier exists only for tests and smoke checks, not production classification.

WSL2/Linux remains portable but is not the primary path because WSL enumeration was unavailable during the initial Windows audit. On a future Linux/VM host, use the official CUDA `llama.cpp` server image or native binary and keep the endpoint private.

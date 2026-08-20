# Local LLM

Recommended Windows runtime is Ollama bound to `127.0.0.1`. The high-volume source deployment uses `qwen3.5:4b` with a 4,096-token context; `qwen3.5:9b` remains the higher-quality option after a stable GPU runtime is validated. The native Ollama API receives the full JSON schema and `think: false`, avoiding hidden reasoning latency. Configure it with:

```dotenv
LLM_PROVIDER=ollama
LLM_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=qwen3.5:4b
LLM_TIMEOUT_SECONDS=45
LLM_MAX_INPUT_CHARS=2000
LLM_CONTEXT_LENGTH=4096
```

Ollama requests keep the model loaded for 15 minutes, cap input at 2,000 characters, context at 4,096 tokens,
and generation at 160 tokens. A timed-out request is not repeated; invalid structured output may be retried once.

On the audited Tesla V100 Windows host, the stable deployment profile uses the CUDA 12 runner selected
automatically by Ollama, NVIDIA driver 582.78, `qwen3.5:4b`, one loaded model, one parallel request and a
4,096-token context. The profile completed sustained real-source collection after earlier driver-level failures
with a different Ollama/runtime combination. Do not force `OLLAMA_LLM_LIBRARY`; after any `GPU is lost` error,
stop the Worker and Ollama and reboot Windows before further inference.

`llama.cpp` remains supported through the OpenAI-compatible provider:

Suggested command:

```powershell
llama-server.exe -m C:\models\Qwen3-8B-Q4_K_M.gguf -ngl 99 -c 4096 --host 127.0.0.1 --port 8080
```

Set `LLM_PROVIDER=openai` and use the `/v1` base URL for llama.cpp or another compatible server. The application sends temperature `0.1`, seed `42`, constrained JSON, retries once, and stores model/prompt identity. `weather-signals collect --max-runtime-seconds N` safely bounds a collection run; a partial run does not advance the source cursor. The offline rules classifier exists only for tests and smoke checks, not production classification.

WSL2/Linux remains portable but is not the primary path because WSL enumeration was unavailable during the initial Windows audit. On a future Linux/VM host, use the official CUDA `llama.cpp` server image or native binary and keep the endpoint private.

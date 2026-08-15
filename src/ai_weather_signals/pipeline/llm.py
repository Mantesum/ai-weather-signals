import json
from hashlib import sha256
from typing import Any

import httpx

from ..config import Settings
from ..metrics import metrics
from ..schemas import LLMExtraction

PROMPT_VERSION = "weather-extraction-v1"
SYSTEM_PROMPT = """You classify a public message about actual weather. Return only schema-valid JSON.
An event is a candidate only for a current personal/probable personal observation or an official current report.
Reject forecasts, old events, news retellings, questions, negations, jokes, metaphors, ads, spam and copies.
Infer a place only when stated or strongly implied by source region. Use ISO-8601 with timezone for observed_at.
Do not include personal data. /no_think"""


class LLMClassifier:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=90)

    @property
    def prompt_hash(self) -> str:
        return sha256(SYSTEM_PROMPT.encode()).hexdigest()

    def classify(self, text: str, source_region: str | None, published_at: str) -> LLMExtraction:
        schema = LLMExtraction.model_json_schema()
        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {"text": text, "source_region": source_region, "published_at": published_at},
                    ensure_ascii=False,
                ),
            },
        ]
        payload: dict[str, Any] = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": 0.1,
            "seed": 42,
            "max_tokens": 500,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "weather_signal", "strict": True, "schema": schema},
            },
        }
        headers = (
            {"Authorization": f"Bearer {self.settings.llm_api_key}"} if self.settings.llm_api_key else {}
        )
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                response = self.client.post(
                    f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return LLMExtraction.model_validate_json(content)
            except (httpx.HTTPError, KeyError, TypeError, ValueError) as error:
                last_error = error
                metrics.inc("llm_invalid_or_failed_responses")
                messages.append(
                    {
                        "role": "user",
                        "content": "Previous output was invalid. Return one schema-valid JSON object only.",
                    }
                )
        metrics.inc("llm_exhausted_retries")
        raise RuntimeError(f"LLM returned no valid extraction: {last_error}")

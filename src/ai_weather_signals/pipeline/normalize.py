import hashlib
import hmac
import re
import unicodedata


def normalized_text(text: str) -> str:
    value = unicodedata.normalize("NFKC", text)
    value = re.sub(r"https?://\S+", " ", value.lower())
    value = re.sub(r"[@#]\w+", lambda match: match.group(0)[1:], value)
    return " ".join(value.split())


def text_hash(text: str) -> str:
    return hashlib.sha256(normalized_text(text).encode()).hexdigest()


def author_hash(source: str, author_id: str | None, salt: str) -> str | None:
    if not author_id:
        return None
    return hmac.new(salt.encode(), f"{source}:{author_id}".encode(), hashlib.sha256).hexdigest()


def safe_excerpt(text: str | None, limit: int = 180) -> str | None:
    if not text:
        return None
    value = " ".join(text.split())
    return value[:limit] + ("…" if len(value) > limit else "")

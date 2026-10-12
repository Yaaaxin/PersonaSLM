"""Native llama.cpp HTTP adapter. No proxy, redirects, downloads or retries."""
import base64
import json
from http.client import IncompleteRead
import math
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


def _localhost_endpoint(base_url: str) -> str:
    if not isinstance(base_url, str) or any(c.isspace() or ord(c) < 32 for c in base_url):
        raise ValueError("Invalid endpoint")
    uri = urlsplit(base_url)
    if uri.scheme != "http" or uri.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise ValueError("P0 inference requires a loopback HTTP endpoint")
    if uri.username is not None or uri.password is not None or uri.path not in ("", "/") or uri.query or uri.fragment:
        raise ValueError("Pass the llama-server root URL without credentials, query, fragment or paths")
    if uri.port is not None and not 1 <= uri.port <= 65535:
        raise ValueError("Invalid endpoint port")
    return base_url.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, "Inference redirects are refused", headers, fp)


def validate_token_ids(tokens, *, allow_empty: bool = True) -> list[int]:
    if not isinstance(tokens, list) or any(type(t) is not int or t < 0 for t in tokens):
        raise ValueError("Endpoint must return a list of nonnegative integer token IDs")
    if not tokens and not allow_empty:
        raise ValueError("Tokenizer returned no IDs for a nonempty prompt")
    return tokens


class LlamaClient:
    def __init__(self, endpoint: str, *, timeout: float = 180, audit=None):
        self.endpoint = _localhost_endpoint(endpoint)
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be positive and finite")
        self.timeout = timeout
        self.audit = audit or (lambda kind, data: None)
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, route: str, payload: dict | None = None) -> dict:
        if route not in ("/health", "/props", "/tokenize", "/completion"):
            raise ValueError("Unsupported P0 endpoint route")
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.audit("http_request", {"route": route, "payload": payload})
        request = Request(self.endpoint + route, data=data, headers={"Content-Type": "application/json"})
        started = time.monotonic()
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                status = response.status
                try:
                    body = response.read()
                except IncompleteRead as exc:
                    self.audit("http_response", {"route": route, "status": status, "incomplete": True,
                               "body_base64": base64.b64encode(exc.partial).decode("ascii"), "error": str(exc)})
                    raise
        except HTTPError as exc:
            self.audit("http_response", {"route": route, "status": exc.code,
                       "body_base64": base64.b64encode(exc.read()).decode("ascii"),
                       "error": str(exc), "elapsed_seconds": time.monotonic() - started})
            raise
        except Exception as exc:
            self.audit("http_error", {"route": route, "type": type(exc).__name__, "error": str(exc),
                       "elapsed_seconds": time.monotonic() - started})
            raise
        # Persist original bytes BEFORE JSON decoding or response validation.
        self.audit("http_response", {"route": route, "status": status,
                   "body_base64": base64.b64encode(body).decode("ascii"),
                   "elapsed_seconds": time.monotonic() - started})
        value = json.loads(body.decode("utf-8"))
        if not isinstance(value, dict) or "error" in value:
            raise ValueError("Unexpected inference JSON payload or server error")
        return value

    def tokenize(self, text: str) -> list[int]:
        result = self.request("/tokenize", {"content": text, "add_special": True,
                              "parse_special": False, "with_pieces": False})
        return validate_token_ids(result.get("tokens"), allow_empty=not bool(text))

    def complete(self, token_ids: list[int], *, seed=42, max_new_tokens=96) -> dict:
        validate_token_ids(token_ids, allow_empty=False)
        if type(max_new_tokens) is not int or max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be positive")
        return self.request("/completion", {
            "prompt": token_ids, "n_predict": max_new_tokens, "temperature": 0.0,
            "top_p": 1.0, "seed": seed, "cache_prompt": False, "stop": [],
            "return_tokens": True, "stream": False,
        })


def tokenize(base_url: str, text: str) -> list[int]:
    return LlamaClient(base_url).tokenize(text)


def complete(base_url: str, prompt: str, *, seed: int = 42, max_new_tokens: int = 96) -> dict:
    client = LlamaClient(base_url)
    return client.complete(client.tokenize(prompt), seed=seed, max_new_tokens=max_new_tokens)


def normalize_result(result: dict) -> dict:
    if not isinstance(result.get("content"), str):
        raise ValueError("Completion content must be a string, including for an empty reply")
    raw_stop = result.get("stop_type")
    stop_reason = {"limit": "length", "word": "stop_sequence", "eog": "eos"}.get(raw_stop, raw_stop)
    if stop_reason is None:
        if result.get("stopped_eos") is True:
            stop_reason = "eos"
        elif result.get("stopped_word") is True:
            stop_reason = "stop_sequence"
        elif result.get("stopped_limit") is True:
            stop_reason = "length"
        else:
            stop_reason = "unknown"
    tokens = result.get("tokens")
    if tokens is not None:
        validate_token_ids(tokens)
    return {"raw_response": result["content"], "stop_reason": str(stop_reason),
            "raw_termination": {key: result[key] for key in (
                "stop_type", "stopped_eos", "stopped_word", "stopped_limit", "stopping_word", "stop", "truncated"
            ) if key in result},
            "generated_token_ids": tokens, "tokens_supported": tokens is not None,
            "token_ids_status": "absent" if tokens is None else ("returned" if tokens else "empty_or_unsupported"),
            "timings": result.get("timings", {})}

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from urllib.error import HTTPError

import pytest

from personaslm.inference import LlamaClient, _localhost_endpoint, normalize_result


@pytest.fixture
def http_stub():
    """Actual loopback HTTP transport, deterministic TEST DOUBLE responses; no model."""
    requests = []
    routes = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.do_POST()

        def do_POST(self):
            data = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            requests.append((self.path, json.loads(data) if data else None))
            status, body, headers = routes.get(self.path, (404, b"missing", {}))
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", routes, requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_token_ids_roundtrip_and_explicit_special_policy(http_stub, monkeypatch):
    endpoint, routes, requests = http_stub
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    routes["/tokenize"] = (200, b'{"tokens": [1, 20, 42]}', {})
    routes["/completion"] = (200, b'{"content": "test double", "stop_type": "eos"}', {})
    client = LlamaClient(endpoint, timeout=2)
    ids = client.tokenize("test text")
    client.complete(ids)
    assert requests[0][1] == {"content": "test text", "add_special": True, "parse_special": False, "with_pieces": False}
    assert requests[1][1]["prompt"] == ids
    assert requests[1][1]["stop"] == []
    assert requests[1][1]["return_tokens"] is True
    assert requests[1][1]["cache_prompt"] is False


@pytest.mark.parametrize("tokens", [None, [True], [-1], [1.5], ["1"], [{"id": 1}], []])
def test_malformed_tokenizer_fails(http_stub, tokens):
    endpoint, routes, _ = http_stub
    routes["/tokenize"] = (200, json.dumps({"tokens": tokens}).encode(), {})
    with pytest.raises(ValueError):
        LlamaClient(endpoint).tokenize("nonempty")


@pytest.mark.parametrize("endpoint", ["http://localhost:8080?q=1", "http://localhost/#frag",
    "http://localhost:0", "http://localhost:65536", "http://localhost:\n8080", "http://@localhost"])
def test_ambiguous_endpoints_rejected(endpoint):
    with pytest.raises(ValueError):
        _localhost_endpoint(endpoint)


@pytest.mark.parametrize("status,body", [(200, b"not json\xff"), (500, b'{"error":"test failure"}')])
def test_wire_bytes_survive_decode_and_http_failure(http_stub, status, body):
    endpoint, routes, requests = http_stub
    routes["/completion"] = (status, body, {})
    events = []
    client = LlamaClient(endpoint, audit=lambda kind, data: events.append((kind, data)))
    with pytest.raises((ValueError, HTTPError)):
        client.complete([1])
    raw = [data for kind, data in events if kind == "http_response"][0]
    assert base64.b64decode(raw["body_base64"]) == body
    assert raw["status"] == status
    assert len(requests) == 1  # no automatic retries


def test_redirect_never_followed(http_stub):
    endpoint, routes, requests = http_stub
    routes["/tokenize"] = (302, b"redirect body", {"Location": endpoint + "/forbidden"})
    with pytest.raises(HTTPError, match="redirects are refused"):
        LlamaClient(endpoint).tokenize("hello")
    assert len(requests) == 1


def test_failed_request_journaling_prevents_generation(http_stub):
    endpoint, _, requests = http_stub

    def disk_full(*_):
        raise OSError("test disk full")

    with pytest.raises(OSError, match="disk full"):
        LlamaClient(endpoint, audit=disk_full).complete([1])
    assert requests == []


def test_partial_http_body_is_preserved(http_stub):
    endpoint, routes, _ = http_stub
    routes["/completion"] = (200, b'{"content": "partial', {"Content-Length": "1000"})
    events = []
    from http.client import IncompleteRead
    with pytest.raises(IncompleteRead):
        LlamaClient(endpoint, audit=lambda kind, data: events.append((kind, data))).complete([1])
    raw = next(data for kind, data in events if kind == "http_response")
    assert raw["incomplete"] is True
    assert base64.b64decode(raw["body_base64"]) == b'{"content": "partial'


@pytest.mark.parametrize("raw,expected", [("limit", "length"), ("word", "stop_sequence"), ("eos", "eos")])
def test_raw_termination_preserved(raw, expected):
    result = normalize_result({"content": "", "stop_type": raw, "stopping_word": "\n"})
    assert result["stop_reason"] == expected
    assert result["raw_termination"]["stop_type"] == raw
    assert result["raw_termination"]["stopping_word"] == "\n"
    assert result["generated_token_ids"] is None
    assert not result["tokens_supported"]


@pytest.mark.parametrize("content", [None, 0, [], {}])
def test_content_type_cannot_be_silently_empty(content):
    with pytest.raises(ValueError):
        normalize_result({"content": content})

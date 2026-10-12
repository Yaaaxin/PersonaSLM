import pytest
from personaslm.inference import _localhost_endpoint, normalize_result


def test_no_nonlocal_inference():
    for endpoint in ("https://example.org", "http://192.168.1.1:8080", "http://localhost:8080/evil", "http://user:password@localhost:8080"):
        with pytest.raises(ValueError):
            _localhost_endpoint(endpoint)


def test_local_inference_allowed():
    assert _localhost_endpoint("http://127.0.0.1:8080/") == "http://127.0.0.1:8080"


def test_normalized_eos():
    r = normalize_result({"content": "", "stopped_eos": True})
    assert r["stop_reason"] == "eos"
    assert r["raw_response"] == ""

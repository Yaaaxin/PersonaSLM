import base64
import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location("boundary_tool_under_test", Path(__file__).resolve().parents[1]/"tools/p0_turn_boundary.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def pair(route, status):
    return [{"kind":"http_request", "data":{"route":route,"payload":{"test_only":True}}},
            {"kind":"http_response", "data":{"route":route,"status":status,
                "body_base64":base64.b64encode(b'{"tokens":[1,2]}').decode(),"elapsed_seconds":0.01}}]


def test_loading_health_503_does_not_invalidate_completed_inference():
    result = module.inference_http_records(pair("/health",503)+pair("/tokenize",200))
    assert len(result)==1 and result[0]["route"]=="/tokenize"


def test_failed_generation_is_not_ignored_like_health_check():
    with pytest.raises(AssertionError):
        module.inference_http_records(pair("/completion",503))

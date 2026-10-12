import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import tempfile
import pytest
from personaslm.provenance import repository_root, require_local_path


@pytest.fixture
def local_tmp():
    """Disposable tests only; every cleanup target is verified inside the project."""
    parent = require_local_path(repository_root() / "results/unit-fixtures")
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="test-", dir=parent) as directory:
        yield require_local_path(Path(directory))

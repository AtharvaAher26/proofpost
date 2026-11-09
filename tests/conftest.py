import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def raw_events() -> list[dict]:
    return json.loads((FIXTURES / "events.json").read_text(encoding="utf-8"))

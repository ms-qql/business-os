import os
import subprocess
import sys
from pathlib import Path


def test_empty_email_key_does_not_block_app_startup():
    backend = Path(__file__).resolve().parent.parent
    env = {**os.environ, "EMAIL_CREDENTIALS_KEY": ""}
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"], cwd=backend, env=env,
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

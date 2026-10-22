"""Record the exact candidate tree and the bytes of each production artifact."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

files = sorted(Path("web/dist").rglob("*"))
checksums = {
    str(f.relative_to("web/dist")): hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.is_file()
}
result = {
    "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "workflow_run": os.getenv("GITHUB_RUN_ID"),
    "data_mode": os.getenv("VITE_DATA_MODE", "demo"),
    "files": checksums,
    "artifact_tree_sha256": hashlib.sha256(json.dumps(checksums, sort_keys=True).encode()).hexdigest(),
}
path = Path("docs/verification/build-evidence.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(result, indent=2) + "\n")
print(result["artifact_tree_sha256"])

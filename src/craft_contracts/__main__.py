from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import DemoManifest
from .runner import InMemoryRunner
from .service import CraftService, create_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local CRAFT control plane")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    service = CraftService()
    manifest = DemoManifest.from_dict(json.loads(args.manifest.read_text(encoding="utf-8")))
    declared = {operation.name: operation.supported for operation in manifest.operations}
    handlers = {
        name: (lambda _request, operation=name: {"operation": operation, "mode": "local-reference"})
        for name, supported in declared.items()
        if supported
    }
    service.register(manifest, InMemoryRunner(manifest, handlers))
    server = create_server(service, args.host, args.port)
    print(f"CRAFT control plane listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

# Publish verified closed-solid STEP files

Use this intake workflow when a downstream CAD or CAM job requires closed
solids. The example stages the STEP beside the destination and publishes
it only after the conversion and its reported verification pass.

The policy requires a clean conversion, watertight input, at least one
output solid, and zero open shells. It requires the B-Rep check to have
run and a measured STEP read-back volume delta. Pass `--expected-solids`
when the job expects an exact number of bodies.

`watertight` describes the input mesh, while `solids` and `openShells`
describe the written geometry. `volumeDeltaPct` compares the reopened
STEP volume with the B-Rep volume before writing. Use separate
application-specific checks for fidelity to the source mesh.

## Run the example

Save the Python 3 block as `publish_step.py`. From the repository root
with `cad_mesh_recovery` on your `PATH`, run these commands with the
bundled fixtures.

```sh
python3 publish_step.py tests/cube.stl published/cube.step --expected-solids 1
python3 publish_step.py tests/harness/testdata/two_cubes.stl \
  published/two-cubes.step --expected-solids 2
```

On success the script prints a JSON object with the published path and
solid count. If a check fails, it returns a nonzero exit code and keeps
any file already at the destination. A successful run replaces that
file. Staging and publication use the same filesystem so readers see
the replacement as a single rename on filesystems that support it.

```python
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path


def check_geometry(result, expected_solids):
    if not result["watertight"] or result["openShells"] or result["solids"] < 1:
        raise ValueError("expected watertight input and closed solid output")
    if expected_solids is not None and result["solids"] != expected_solids:
        raise ValueError(f"expected {expected_solids} solids, got {result['solids']}")
    if result.get("validityCheck") == "skipped":
        raise ValueError("B-Rep validity check was skipped")
    delta = result["volumeDeltaPct"]
    if not math.isfinite(delta) or delta < 0:
        raise ValueError("STEP read-back volume was not measured")


def publish_step(source, destination, expected_solids=None):
    source = source.resolve()
    destination = destination.absolute()
    if source == destination.resolve():
        raise ValueError("use a different path for the STEP destination")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".step-stage-", dir=destination.parent
    ) as directory:
        staged = Path(directory) / destination.name
        completed = subprocess.run(
            ["cad_mesh_recovery", str(source), "-o", str(staged), "--quiet"],
            capture_output=True,
            text=True,
        )
        prefix = "RESULT "
        line = completed.stdout.strip()
        if not line.startswith(prefix):
            raise RuntimeError(completed.stderr.strip() or "missing RESULT line")
        result = json.loads(line[len(prefix):])
        if completed.returncode != 0 or not result["ok"] or result.get("warnings"):
            detail = result.get("error") or completed.stderr.strip()
            raise RuntimeError(detail or "conversion did not complete cleanly")

        check_geometry(result, expected_solids)
        if not staged.is_file() or staged.stat().st_size == 0:
            raise RuntimeError("conversion did not produce a staged STEP file")
        staged.replace(destination)

    return {"output": str(destination), "solids": result["solids"]}


def main():
    parser = argparse.ArgumentParser(description="Publish a verified closed-solid STEP")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--expected-solids", type=int)
    args = parser.parse_args()
    if args.expected_solids is not None and args.expected_solids < 1:
        parser.error("--expected-solids must be positive")
    try:
        summary = publish_step(args.source, args.destination, args.expected_solids)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"error: {error}\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
```

"""Convert an STL directory with the CAD Mesh Recovery CLI."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def convert_one(cli, units, source_dir, output_dir, source):
    relative_input = source.relative_to(source_dir)
    relative_output = relative_input.with_name(relative_input.name + ".step")
    output = output_dir / relative_output
    row = {
        "input": relative_input.as_posix(),
        "output": relative_output.as_posix(),
        "status": "failed",
    }

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Output already exists: {output}")
        run = subprocess.run(
            [cli, str(source), "-o", str(output), "--units", units, "--quiet"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        row["error"] = str(error)
        return row

    row["exitCode"] = run.returncode
    if run.stderr:
        row["stderr"] = run.stderr.rstrip("\r\n")

    line = run.stdout.rstrip("\r\n").rsplit("\n", 1)[-1]
    prefix = "RESULT "
    result = None
    if line.startswith(prefix):
        try:
            result = json.loads(line[len(prefix):])
        except json.JSONDecodeError:
            pass

    if not isinstance(result, dict):
        row["error"] = "Missing or invalid RESULT line"
    else:
        row["result"] = result
        if run.returncode not in (0, 2) or result.get("ok") is not True:
            row["error"] = result.get("error") or f"Conversion exited with {run.returncode}"
        elif not output.is_file():
            row["error"] = "No STEP file at the requested output path"
        else:
            row["status"] = "warnings" if run.returncode == 2 else "clean"
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="directory containing STL files")
    parser.add_argument("destination", type=Path, help="new directory for STEP files")
    parser.add_argument("--cli", default="cad_mesh_recovery", help="conversion executable")
    parser.add_argument("--units", choices=("mm", "in"), default="mm", help="STL units")
    args = parser.parse_args()

    cli = shutil.which(args.cli)
    if cli is None:
        parser.error(f"conversion executable not found: {args.cli}")
    source_dir = args.source.resolve()
    if not source_dir.is_dir():
        parser.error(f"input directory does not exist: {args.source}")
    sources = sorted(
        path for path in source_dir.rglob("*")
        if path.suffix.lower() == ".stl" and path.is_file()
    )
    if not sources:
        parser.error(f"no STL files found below {args.source}")

    output_dir = args.destination.absolute()
    try:
        output_dir.mkdir()
    except OSError as error:
        parser.error(f"cannot create destination directory: {error}")

    failed = False
    for source in sources:
        row = convert_one(cli, args.units, source_dir, output_dir, source)
        failed = failed or row["status"] == "failed"
        print(json.dumps(row), flush=True)
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())

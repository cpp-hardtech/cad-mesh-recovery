# Batch STL conversion

Use the [Python example](examples/batch_convert.py) to convert a directory of
STL files with the CLI and save an outcome for each file. It uses the Python
standard library and an existing `cad_mesh_recovery` executable.

```sh
python3 docs/examples/batch_convert.py "./incoming meshes" ./step-output \
  --cli ./build/cad_mesh_recovery --units mm > batch.jsonl
```

The destination directory must be new and its parent must exist. The example
recurses through the input directory and mirrors its layout. It appends
`.step` to each full input filename, so `left/part.stl` and `right/part.stl`
produce `left/part.stl.step` and `right/part.stl.step`. The `--units` setting
applies to the entire batch.

Standard output is JSON Lines, with one record per discovered STL in path
order. The `input` and `output` paths are relative to their respective roots. Each
record has a `status` of `clean` for CLI exit 0, `warnings` for a STEP
written with CLI exit 2, or `failed` when conversion could not be confirmed.
The record includes the CLI exit code, diagnostics, and parsed `RESULT`
when available. Use records with `clean` or `warnings` status to locate the
produced STEP files and inspect `result` for warning and validity details.

Processing continues after per-file failures. The batch exits 0 when every
input produces a STEP and 1 when any input fails. Argument and setup errors
exit 2. Conversion uses the CLI's default STEP read-back verification.

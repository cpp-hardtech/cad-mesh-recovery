# Contributing

Thanks for your interest in CAD Mesh Recovery.

## Before you start

Open an issue describing the change you plan to make. For anything beyond a small fix, agree
on the approach first so the work is not rejected after it is done.

## Workflow

1. Create a topic branch off the default branch.
2. Keep a pull request to one logical change.
3. Build and run the tests locally, with the `dev` preset:

   ```sh
   cmake --preset dev
   cmake --build --preset dev --config Release
   ctest --preset dev -C Release
   ```

4. In the pull request description, state what changed and how you verified it.

## Code style

Match the formatting of the surrounding code. C++ sources follow the `.clang-format`
configuration in this repository where one is present; run it before committing.

## Geometry changes

Changes to reconstruction or healing behaviour need a test case that fails before the change
and passes after it. Prefer a small mesh that isolates the behaviour over a large fixture. Note
in the pull request which OCCT version you validated against, because the calibrated tests are
tied to OCCT 7.9.x.

## License

This project is a derivative work; its provenance and license terms are recorded in
[NOTICE](NOTICE) and [LICENSE](LICENSE). By submitting a contribution you agree that it is
licensed under the terms in LICENSE and that those provenance notes are kept intact.

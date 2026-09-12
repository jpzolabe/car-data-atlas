# fixtures/

Sample data for tests only - never real data, never anything that could be
mistaken for it. Per rule zero in `CLAUDE.md`:

> If sample data is genuinely needed for a test, put it under `fixtures/` with
> obviously fake values (e.g. `999999`) and never in `data/`.

Nothing here yet - add fixtures alongside the pipeline/site code that needs
them, once there's a test that needs one. Don't pre-populate this folder
speculatively.

# Change Summary

Full diff can be found [here.](https://github.com/latchbio/ProteinCartography/pull/1/files)

## Workflow-level Changes

- Move all `from tests import mocks` into the `if` blocks used for testing. This import path calls `file_utils.find_repo_dirpath` as a side-effect which fails in non-local execution environments.
- Add `LPath` logic to manually download `input_dir` from latch. This is so that input functions that use `Path.glob` work as expected.
- Configure a `REMOTE_OUTPUT_DIR` in addition to `OUTPUT_DIR` to contol which outputs get written back to Latch Data.
- Use `storage.latch` on certain outputs of rules to configure them to write to Latch Data.
- Use `os.path.join` over `Path.__truediv__` because the latter collapses multiple slashes (which breaks Latch URLs that depend on the prefix `latch://`).

## Environment Changes

- Use a modified version of the environment in `envs/cartography_tidy.yml`:
  - Update to `python=3.11`
  - Drop `ipython`, `mamba`, and `pip` dependencies
  - Add `snakemake`, `latch`, `snakemake-executor-plugin-latch`, and `snakemake-storage-plugin-latch` (installed externally in the `Dockerfile` using `pip`)

## New Files

- SDK required files:
  - `Dockerfile`
  - `wf/`
  - `latch_metadata/`
  - `version`
  - `.dockerignore`

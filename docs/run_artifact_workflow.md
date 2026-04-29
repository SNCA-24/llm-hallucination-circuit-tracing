# Run Artifact Workflow

`outputs/examples_registry.csv` is the canonical project state. Routine experiment output should not be written into `docs/` or scattered across top-level `outputs/` files. Stage runs write their raw artifacts under `outputs/runs/<run_id>/`, then write concise status updates back to the registry.

## Why Run Folders Exist

Run folders make experiments rerunnable and auditable without turning the registry into a raw-output store. The registry answers "what is the latest state of this example?" The run folder answers "what exactly happened in this execution?"

The default run ID format is:

```text
YYYYMMDD_HHMMSS_<stage>_<short_scope>
```

Examples:

```text
20260425_221530_token_span_813_3573
20260425_223900_pair_validation_813_3573
```

If the generated folder already exists, the script appends a numeric suffix such as `_2`.

## Run Folder Contents

Each run folder contains:

- `manifest.json`: run metadata, input registry path, target IDs, model alias when applicable, artifact paths, status, notes, and whether backward compatibility mode was used.
- `summary.json`: processed/skipped breakdown, parameter hash, run status, and per-example artifact pointers.
- Stage-specific artifacts such as `token_span_results.jsonl` or `pair_validation_results.jsonl`.
- Optional duplicate legacy outputs only when explicitly requested by old CLI flags.

`manifest.json` may show `status=running` while a run is active or interrupted. A completed run should end as `success`, `partial`, `failed`, or `skipped` when no rows were attempted because all selected rows were already done or ineligible.

## Registry Interaction

Stage scripts read candidate selection from `outputs/examples_registry.csv`, apply optional CLI filters, and write short status summaries back to the same registry. Full prompts, generations, token diagnostics, and error details stay in the run folder.

The latest artifact for an example is found by checking:

1. `latest_artifact_root` in `outputs/examples_registry.csv`
2. `<latest_artifact_root>/manifest.json`
3. `<latest_artifact_root>/summary.json`
4. The stage-specific path in `artifact_paths`

The registry also keeps stage-specific fields such as `token_mapping_status`, `validated_pair_flag`, `validation_results_path`, and `tracing_status`.

Registry rebuilds preserve live experiment state by default. Running:

```bash
python3 scripts/build_examples_registry.py
```

re-merges the source sheets but carries forward existing stage-owned fields such as latest run pointers, token-span status, pair-validation status, validation result paths, final workflow status, keep reasons, and tracing status from the current `outputs/examples_registry.csv`.

Use reset mode only when intentionally discarding live run state and returning to source-sheet defaults:

```bash
python3 scripts/build_examples_registry.py --reset
```

## Resume And Rerun

Interrupted runs leave a run folder behind. Inspect its `manifest.json` and `summary.json` if present. A later run gets a new run ID; it does not overwrite the interrupted folder.

By default, scripts skip terminal rows and matching prior successful artifacts. Use `--force` when an intentional rerun is needed.

Dry-run commands show the selected rows and skip reasons without writing artifacts or updating the registry:

```bash
python3 scripts/run_token_span_check.py --example-ids 813 3573 --dry-run
python3 scripts/run_pair_validation.py --example-ids 813 3573 --dry-run
```

To rerun failed examples from a previous pair-validation run:

```bash
python3 scripts/run_pair_validation.py --rerun-failed-from-run 20260425_223900_pair_validation_813_3573 --force
```

## Current Refactored Stages

Token-span feasibility:

```bash
python3 scripts/run_token_span_check.py --example-ids 813 3573
```

Pair validation:

```bash
python3 scripts/run_pair_validation.py --example-ids 813 3573
```

If no pair-validation IDs are provided, the script defaults to registry rows with `validation_target_flag=true`.

After pair validation, rows are removed from the validation target queue. Passing rows get `validation_target_flag=false`, `validated_pair_flag=true`, `final_status=validated`, and `keep_reason=Validated clean/corrupted pair.` Failed validation gates get `validation_target_flag=false`, `validated_pair_flag=false`, `final_status=processed_reject`, and a concise failure reason. Infrastructure or pre-completion failures are parked so they can be retried intentionally.

Forward pass:

```bash
python3 scripts/run_forward_pass_pilot.py --input outputs/runs/<tracing_prep_run_id>/tracing_pilot_input.json
```

Layer patching:

```bash
python3 scripts/run_layer_patching_pilot.py \
  --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt \
  --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json
```

Layer patching patches corrupted-run hidden states into the clean run at the aligned causal prediction position from the forward-pass artifact. It remains a single-example stage and writes `layer_patching_results.jsonl`, `layer_patching_summary.md`, `manifest.json`, and `summary.json` under a fresh run folder.

Head patching:

```bash
python3 scripts/run_head_patching_pilot.py \
  --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt \
  --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json \
  --layer-results outputs/runs/<layer_patching_run_id>/layer_patching_results.jsonl
```

Use `--layers 30 29 31` to override automatic top-layer selection from the layer results. Head patching writes `head_patching_results.jsonl`, `head_patching_summary.md`, `manifest.json`, and `summary.json` under a fresh run folder. It does not run ablations.

Head ablation:

```bash
python3 scripts/run_head_ablation_pilot.py \
  --input-pt outputs/runs/<forward_pass_run_id>/forward_pass_pilot.pt \
  --metadata outputs/runs/<forward_pass_run_id>/tracing_pilot_input_with_divergence.json \
  --head-patching-results outputs/runs/<head_patching_run_id>/head_patching_results.jsonl
```

Use `--heads L29H5 L29H21 L31H4 L31H31 L30H31` to override automatic top-head selection. Head ablation writes `head_ablation_results.jsonl`, `head_ablation_summary.md`, `manifest.json`, and `summary.json` under a fresh run folder.

Later tracing stages should adopt the same shape: registry selection, run-folder artifacts, per-example registry updates, and concise `summary.json` breakdowns.

Layer patching now consumes a forward-pass `.pt` artifact plus the matching metadata JSON from a forward-pass run folder and writes its own run folder. The layer stage validates that artifact and metadata example IDs match, that the model alias is `llama-2-7b-chat`, and that the clean/corrupted causal prediction indices are present and in range. Head patching remains a separate later stage.

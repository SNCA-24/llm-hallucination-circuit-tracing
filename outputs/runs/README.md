# Run Artifacts

Routine stage outputs are stored under `outputs/runs/<run_id>/`.

Small reproducibility metadata such as `manifest.json`, `summary.json`, JSONL result summaries, and Markdown summaries may be committed when useful for review. Large tensor/model artifacts are intentionally excluded from Git, including:

- `*.pt`
- `*.safetensors`
- model weight files
- cache folders

The full forward-pass and patching stages require GPU/Colab execution. The registry, run summaries, scripts, and documentation record the completed pilot state and provide enough structure for future examples to be appended through the same workflow.

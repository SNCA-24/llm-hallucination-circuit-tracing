# Pilot Mechanistic Tracing of Prompt-Corrected Hallucination Pairs in Llama-2-7B-Chat

## Abstract

Large language models can produce factual errors that are fluent, plausible, and close to the source context. This pilot study tests whether minimally edited prompts can create controlled clean/corrupted pairs for mechanistic tracing of such hallucinations. In this setup, the clean prompt is the original prompt condition that reproduces a target hallucination, while the corrupted prompt is a minimal factuality-oriented edit that flips the model toward a verified-truth continuation. We evaluate two completed examples in `llama-2-7b-chat` using pair validation, teacher-forced forward-pass alignment, layer patching, head patching, and head ablation. Across the two validated examples, the strongest repeated signal appears at the layer level in late layers around `L29-L30`; however, the strongest head candidates differ by example. These results should be interpreted as pilot evidence over two validated examples, not as statistical generalization or evidence of a stable hallucination circuit.

## 1. Introduction

Hallucinations in language models are difficult to study because factual errors can be sensitive to prompt wording, decoding behavior, tokenization, and source context. A useful mechanistic setup should isolate a contrast where the model produces a target hallucination in one condition and a verified-truth continuation in another closely related condition. This project studies whether minimal prompt corrections can create that contrast reliably enough to support causal tracing.

The central question is:

> Can minimal prompt corrections create validated hallucination/truth pairs that are suitable for mechanistic tracing?

We treat this as a pilot study. The goal is not to claim a general mechanism for hallucination, nor to identify a stable circuit or head family. Instead, the goal is to establish a reusable workflow and report the first completed tracing results under conservative claim boundaries.

This matches the project objective of localizing layers and attention heads that contribute to hallucinated continuations under a validated prompt intervention, while keeping the scope narrow enough for careful interpretation.

This draft makes four contributions:

1. A registry-based workflow for selecting, validating, tracing, and auditing candidate examples.
2. A clean/corrupted pair construction procedure that requires clean hallucination reproduction and corrupted truth flipping before tracing.
3. A two-example tracing pilot for `llama-2-7b-chat`.
4. A conservative cross-example comparison showing repeated late-layer restoration around `L29-L30`, while exact head candidates differ.

Future examples can be added modularly by appending to the evidence table, adding a new Results subsection, and updating the cross-example analysis only when the new example changes the pattern.

## 2. Related Work

Prior work on hallucination and factuality frames language-model errors as cases where generated text is unsupported, contradicted, or otherwise misaligned with the available evidence [TruthfulQA; SelfCheckGPT]. This project focuses on short, concrete factual deviations that can be paired with a verified correction target.

The candidate examples are derived from the RAGTruth/RAGTruth_Xtended workflow, which provides source-grounded examples of model responses and factuality issues suitable for controlled follow-up analysis [RAGTruth; RAGTruthXtended]. The registry layer in this project narrows those candidates to examples with concrete hallucinated spans, feasible token mapping, and a minimal intervention prompt.

The model scope is `llama-2-7b-chat`, a chat-tuned Llama-2 model [Llama2]. Results in this draft are specific to that model and should not be generalized to other checkpoints without additional experiments.

Mechanistically, the tracing stages build on activation patching and causal tracing methods that intervene on internal representations to measure their effect on output logits [ROME; ActivationPatchingBestPractices]. Layer patching is used as a coarse localization step.

The head-level stages follow the same intervention logic at the attention-head level, using head patching and ablation to test candidate components within the late-layer regions identified by layer patching [TransformerCircuits; IOICircuit]. Prompt-sensitivity work also motivates treating prompt edits as meaningful interventions rather than neutral formatting changes [AutoPrompt; PromptOrderSensitivity].

This project uses existing causal tracing ideas as tools. It does not propose a new tracing algorithm. The novelty in the current pilot is the controlled prompt-correction workflow and the operational discipline around validating, storing, and comparing examples.

## 3. Dataset and Model Scope

### 3.1 Source Examples

Admitted examples are derived from the RAGTruth_Xtended/RAGTruth workflow and managed through `outputs/examples_registry.csv`, which is the canonical project state for admitted examples. Candidate examples are admitted only after pre-registry checks confirm that the hallucinated behavior is concrete, relevant to the project scope, and suitable for downstream validation.

The registry tracks:

- candidate provenance,
- clean input text,
- verified ground-truth target,
- hallucinated substring,
- token-span feasibility,
- corrupted prompt candidate,
- pair-validation status,
- tracing status,
- latest run artifacts.

Failed and parked examples are tracked explicitly rather than omitted. This is important because validation failure is a meaningful part of the workflow, not a hidden preprocessing detail.

### 3.2 Model Scope

All completed tracing results in this draft use `llama-2-7b-chat`. The current results should not be generalized to other models, model sizes, chat templates, or decoding settings.

### 3.3 Completed and Excluded Examples

Two examples have completed pair validation and full tracing:

- Example `369`
- Example `813`

Known failed, parked, or ambiguous examples include:

- `51`: failed pair validation.
- `3573`: failed pair validation.
- `93`: parked before full validation/tracing.
- `597`: parked before full validation/tracing.
- `2793`: parked because the correction target was weak.
- `2265`: ambiguous token mapping.
- `2781`: ambiguous token mapping.

Only validated examples are used in the Results and Cross-Example Analysis sections. Excluded examples are summarized in Appendix B.

## 4. Methodology

### 4.1 Registry and Run Artifact Workflow

The project uses a split between canonical state and routine run artifacts. The registry, `outputs/examples_registry.csv`, answers the question: what is the latest state of each example? Run folders under `outputs/runs/<run_id>/` answer the question: what happened in a specific execution?

Each routine run writes artifacts under a run-specific folder. Run IDs follow this format:

```text
YYYYMMDD_HHMMSS_<stage>_<short_scope>
```

Each run folder contains:

- `manifest.json`, with run metadata, inputs, model alias, status, artifact paths, and notes.
- `summary.json`, with processed/skipped breakdowns and concise status information.
- stage-specific artifacts, such as JSONL results or tensor artifacts.

The registry stores concise status summaries and latest artifact pointers, not full raw outputs. This separation is intended to make reruns, partial failures, and future example additions auditable without overwriting prior evidence.

### 4.2 Clean/Corrupted Pair Construction

The clean prompt is the original prompt condition used for validation. In this project, "clean" does not mean factually correct; it means the unmodified baseline condition. A clean prompt is useful only if it reproduces the target hallucination.

The corrupted prompt is a minimally edited intervention prompt, often by adding a factuality-oriented instruction or constraint. In this project, "corrupted" means intervention condition, following causal-tracing terminology. The corrupted prompt is useful only if it flips the model toward the verified-truth target without retaining the hallucinated substring.

An example passes pair validation only if:

1. the clean run reproduces the target hallucination, and
2. the corrupted run flips to the verified truth.

Examples that do not pass this gate are failed or parked and are not traced.

### 4.3 Forward-Pass Alignment

For each validated pair, the workflow performs teacher-forced prompt and output alignment. The purpose is to identify an aligned divergence point where the hallucinated continuation and verified-truth continuation differ.

The tracing stages use the causal prediction index immediately before the divergence token. This is important because the model predicts the next token from the previous position. Forward-pass artifacts store the clean and corrupted absolute divergence token indices and prediction indices, and downstream stages consume those indices directly.

### 4.4 Layer Patching

Layer patching patches corrupted-run hidden states into the clean run at the aligned causal prediction position. The restoration score is based on a truth-minus-hallucination logit margin:

```text
baseline_margin = verified_truth_logit - hallucinated_logit
patched_margin = patched_verified_truth_logit - patched_hallucinated_logit
restoration_score = patched_margin - baseline_margin
```

A higher restoration score indicates that the patched activation moved the clean run more toward the verified-truth token relative to the hallucinated token. This is a localization signal, not proof of a complete mechanism.

### 4.5 Head Patching

Head patching is a finer-grained follow-up to layer patching. It patches one attention head at a time from the corrupted run into the clean run, again at the aligned prediction position. Candidate heads are ranked by the same restoration-score logic used for layer patching.

The current pilot treats head-patching results as candidate localization evidence. It does not assume that the strongest head in one example will also be strongest in another.

### 4.6 Head Ablation

Head ablation tests candidate heads by suppressing selected head contributions in the clean run. The ablation score is:

```text
baseline_margin = verified_truth_logit - hallucinated_logit
ablated_margin = ablated_verified_truth_logit - ablated_hallucinated_logit
ablation_score = ablated_margin - baseline_margin
```

In this project, ablation is used as a follow-up check on candidate heads from patching. It should not be interpreted as a full causal proof of a circuit, especially with only two completed examples.

## 5. Experimental Setup

The heavy model stages were run in Colab where needed, while routine project state and saved artifacts are organized locally through the registry and run folders.

The tracing lifecycle is:

1. Candidate admission into the registry.
2. Token-span feasibility check.
3. Human review and minimal corrupted prompt authoring.
4. Pair validation.
5. Tracing prep.
6. Forward-pass alignment.
7. Layer patching.
8. Head patching.
9. Head ablation.

| Stage | Purpose | Output |
| --- | --- | --- |
| Registry admission | Track approved examples and metadata | Canonical row in `outputs/examples_registry.csv` |
| Token-span feasibility | Check whether the hallucinated span can be mapped cleanly to tokens | Token mapping status and span fields |
| Pair validation | Confirm clean hallucination reproduction and corrupted truth flip | Validation status and JSONL result artifact |
| Tracing prep | Package validated prompts and targets for tracing | `tracing_pilot_input.json` |
| Forward pass | Align clean/corrupted outputs and divergence indices | Tensor artifact and divergence metadata |
| Layer patching | Localize layer-level restoration signal | Layer results JSONL and summary |
| Head patching | Test candidate attention heads | Head results JSONL and summary |
| Head ablation | Evaluate candidate head influence in clean run | Ablation results JSONL and summary |

The current report evaluates only examples that completed the validation and tracing lifecycle. Results are reported using:

- validation outcome,
- divergence token,
- top restoring layers,
- top restoring heads,
- best ablation result,
- conservative interpretation.

Results are reported as pilot evidence over validated examples, not as statistical generalization.

## 6. Results

### 6.1 Example 369

Example `369` targets a hallucinated film-title completion. The hallucinated target is:

```text
1986 John Hughes film "Pretty in Pink"
```

The verified correction target is:

```text
1986 John Hughes film
```

The pair passed validation: the clean run reproduced the target hallucination, and the corrupted run flipped to the verified truth without retaining the hallucinated substring. The model scope is `llama-2-7b-chat`.

The divergence target for this example is:

- Output-relative divergence token index: `22`
- Hallucinated token at divergence: `"` (id `376`)
- Verified-truth token at divergence: `,` (id `29892`)

The top restoring layers were:

| Rank | Layer | Restoration score |
| ---: | --- | ---: |
| 1 | `L30` | `16.460938` |
| 2 | `L29` | `16.390625` |
| 3 | `L23` | `15.804688` |

The top restoring heads were:

| Rank | Head | Restoration score |
| ---: | --- | ---: |
| 1 | `L30H26` | `0.507812` |
| 2 | `L23H3` | `0.453125` |
| 3 | `L23H10` | `0.250000` |
| 4 | `L29H26` | `0.234375` |
| 5 | `L29H5` | `0.187500` |

The best single-head ablation was `L23H3` with ablation score `1.757812`. The best multi-head ablation was `pair_L30H26_L23H3` with score `3.046875`.

For this example, late layers `L30` and `L29` showed strong restoration, while `L23` also appeared prominently. The ablation effects were larger than in example `813`. This is strong pilot signal for this single example, but it should not be generalized by itself.

### 6.2 Example 813

Example `813` targets a hallucinated legal-charge completion. The hallucinated target is:

```text
10 counts of fraud
```

The verified correction target is:

```text
two counts of offering a false instrument for filing in the first degree
```

The pair passed validation: the clean run reproduced the target hallucination, and the corrupted run flipped to the verified truth without retaining the hallucinated substring. The model scope is `llama-2-7b-chat`.

The divergence target for this example is:

- Output-relative divergence token index: `16`
- Hallucinated divergence token: tokenizer boundary / whitespace-like token id `29871`
- Verified-truth token at divergence: `two` (id `1023`)

The tokenizer detail for id `29871` should be interpreted carefully. The meaningful comparison is the aligned prediction contrast between the hallucinated continuation and the verified-truth continuation, not the human-readable decoded surface form of the boundary-like token.

The top restoring layers were:

| Rank | Layer | Restoration score |
| ---: | --- | ---: |
| 1 | `L30` | `8.250000` |
| 2 | `L29` | `8.203125` |
| 3 | `L31` | `7.875000` |

The top restoring heads were:

| Rank | Head | Restoration score |
| ---: | --- | ---: |
| 1 | `L29H5` | `0.554688` |
| 2 | `L29H21` | `0.140625` |
| 3 | `L31H4` | `0.085938` |
| 4 | `L31H31` | `0.062500` |
| 5 | `L30H31` | `0.054688` |

The best single-head ablation was `L29H5` with score `0.257812`. The best multi-head ablation was `top3_heads` with score `0.179688`. The top-3 multi-head ablation was weaker than the best single-head ablation, suggesting that the selected heads do not combine additively in this pilot setting.

For this example, the strongest layer-level signal again appeared in late layers around `L29-L30`, with `L31` also present among top layers. The head-level signal differed from example `369`, with `L29H5` strongest for this example. Ablation effects were smaller than for example `369`.

### 6.3 Future Example N

Future completed examples should be added using the same structure:

- hallucination and correction target,
- validation outcome,
- divergence target,
- top restoring layers,
- top restoring heads,
- best ablation result,
- conservative interpretation.

The evidence table and cross-example comparison should be updated only after the example passes pair validation and completes the tracing stages.

## 7. Cross-Example Analysis

Both completed examples passed the same validation criterion: the clean run reproduced the target hallucination and the corrupted run flipped to the verified truth. This makes the two examples comparable as controlled prompt-correction pairs, although the content, tokenization, and score magnitudes differ.

At the layer level, both examples implicate late layers around `L29-L30`:

| Example | Strongest layers |
| --- | --- |
| `369` | `L30`, `L29`, `L23` |
| `813` | `L30`, `L29`, `L31` |

This is the strongest repeated pattern in the current pilot. It suggests that late-layer representations around `L29-L30` are useful places to inspect in future examples. It does not establish that those layers are a general hallucination mechanism.

At the head level, the examples differ:

| Example | Strongest heads |
| --- | --- |
| `369` | `L30H26`, `L23H3`, `L23H10`, `L29H26`, `L29H5` |
| `813` | `L29H5`, `L29H21`, `L31H4`, `L31H31`, `L30H31` |

`L29H5` appears in both result sets, but it is strongest for `813` and only a secondary candidate for `369`. The strongest repeated signal is therefore layer-level, not head-level: both examples implicate late layers around `L29-L30`, but the exact heads differ.

Ablation strength also differs substantially:

| Example | Best single-head ablation | Best multi-head ablation |
| --- | --- | --- |
| `369` | `L23H3`, score `1.757812` | `pair_L30H26_L23H3`, score `3.046875` |
| `813` | `L29H5`, score `0.257812` | `top3_heads`, score `0.179688` |

This difference may indicate that the relevant signal is more concentrated in the tested heads for `369` than for `813`, or that the current ablation setup interacts differently with the two examples. With only two examples, this remains an interpretation to test, not a claim.

The current evidence therefore supports prioritizing late-layer inspection in future examples, while treating head-level candidates as example-specific until more data are added.

## 8. Discussion

The main value of the current pilot is the controlled workflow. By requiring pair validation before tracing, the project avoids tracing examples where the clean/corrupted contrast is not actually present. By storing outputs in run folders and keeping registry status concise, the project also avoids relying on ad hoc CSVs or overwritten run logs.

The workflow itself is a contribution because it converts candidate hallucinations into validated clean/corrupted tracing examples. Instead of starting from an interesting error and immediately tracing it, the process verifies that the hallucination reproduces, that a minimal intervention flips the answer, and that the example has the token-level structure required for downstream patching.

The two completed examples provide a useful early pattern. Both show strong layer-level restoration in late layers around `L29-L30`. This repeated layer-level signal is a reasonable hypothesis for the next round of tracing. However, the exact head candidates differ, and the ablation strength differs substantially. The current evidence therefore supports continued inspection of late layers, but not a stable head-level circuit claim.

The clean/corrupted terminology is also important. In this project, clean refers to the original prompt condition, not factual correctness. Corrupted refers to the intervention condition, even though that intervention is designed to produce a more factual answer. This convention is useful for causal tracing, but it should be explained clearly in presentations and writing.

The failed and parked examples matter for interpretation. They show that successful tracing examples are not automatic: pair validation can fail, correction targets can be weak, and token mapping can be ambiguous. As the pilot scales, these exclusions should continue to be documented.

## 9. Limitations

This study has several important limitations.

First, only two examples have completed the full tracing workflow. The results are pilot evidence and cannot support statistical generalization.

Second, all completed tracing results are from `llama-2-7b-chat`. The findings should not be generalized to other models, model families, or model sizes.

Third, pair validation is brittle. A prompt may be scientifically promising but fail because the clean run does not reproduce the target hallucination or because the corrupted run does not flip cleanly to the verified truth.

Fourth, tokenization complicates interpretation. Example `813` has a divergence token corresponding to a tokenizer boundary / whitespace-like token id `29871`. The aligned prediction contrast remains useful, but the decoded token itself should not be over-interpreted.

Fifth, head-level results are not stable across the two examples. The current evidence does not identify a shared head-level circuit.

Finally, the current workflow tests selected factuality corrections and does not evaluate broad hallucination categories, production mitigation, or downstream user-facing reliability.

## 10. Ethical Considerations

This project studies factuality failures and model internals in a controlled research setting. The findings should not be presented as a production hallucination detector, a safety guarantee, or evidence that the model's factual behavior is fully understood.

The examples involve generated summaries of real-world content. Such outputs can contain misleading or sensitive claims if reused outside the controlled validation context. Care should be taken not to amplify hallucinated statements as if they were factual.

There is also an interpretability communication risk: mechanistic results can sound more definitive than they are. This report therefore uses conservative language and explicitly avoids claiming a stable circuit, stable head, or broad mechanism.

No deployment or user-facing decision system is proposed in this pilot.

## 11. Conclusion

This pilot study builds a reusable workflow for tracing prompt-corrected hallucination pairs in `llama-2-7b-chat`. Two examples, `369` and `813`, completed pair validation and full tracing through head ablation. In both examples, the strongest repeated signal appears at the layer level in late layers around `L29-L30`. The exact head candidates differ, and the ablation strengths differ, so the evidence does not support a stable circuit or stable head claim.

The next step is to add more validated examples using the same registry and run-folder workflow. Future examples should be appended to the evidence table and cross-example analysis rather than retrofitted into the current two-example interpretation.

## References

- [ActivationPatchingBestPractices] Fred Zhang and Neel Nanda. 2024. *Towards Best Practices of Activation Patching in Language Models: Metrics and Methods*. International Conference on Learning Representations (ICLR). arXiv:2309.16042. URL: https://arxiv.org/abs/2309.16042.
- [AutoPrompt] Taylor Shin, Yasaman Razeghi, Robert L. Logan IV, Eric Wallace, and Sameer Singh. 2020. *AutoPrompt: Eliciting Knowledge from Language Models with Automatically Generated Prompts*. Proceedings of EMNLP 2020, pages 4222-4235. DOI: 10.18653/v1/2020.emnlp-main.346. URL: https://aclanthology.org/2020.emnlp-main.346/.
- [IOICircuit] Kevin Wang, Alexandre Variengien, Arthur Conmy, Buck Shlegeris, and Jacob Steinhardt. 2023. *Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small*. International Conference on Learning Representations (ICLR). arXiv:2211.00593. URL: https://arxiv.org/abs/2211.00593.
- [Llama2] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, and others. 2023. *Llama 2: Open Foundation and Fine-Tuned Chat Models*. arXiv:2307.09288. URL: https://arxiv.org/abs/2307.09288.
- [PromptOrderSensitivity] Yao Lu, Max Bartolo, Alastair Moore, Sebastian Riedel, and Pontus Stenetorp. 2022. *Fantastically Ordered Prompts and Where to Find Them: Overcoming Few-Shot Prompt Order Sensitivity*. Proceedings of ACL 2022, pages 8086-8098. DOI: 10.18653/v1/2022.acl-long.556. URL: https://aclanthology.org/2022.acl-long.556/.
- [RAGTruth] Cheng Niu, Yuanhao Wu, Juno Zhu, Siliang Xu, KaShun Shum, Randy Zhong, Juntong Song, and Tong Zhang. 2024. *RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models*. Proceedings of ACL 2024, pages 10862-10878. DOI: 10.18653/v1/2024.acl-long.585. URL: https://aclanthology.org/2024.acl-long.585/.
- [RAGTruthXtended] Jakob Snel and Seong Joon Oh. 2025. *First Hallucination Tokens Are Different From Conditional Ones*. arXiv:2507.20836. Dataset/code: RAGTruth_Xtended. URL: https://arxiv.org/abs/2507.20836; https://github.com/jakobsnl/RAGTruth_Xtended.
- [ROME] Kevin Meng, David Bau, Alex Andonian, and Yonatan Belinkov. 2022. *Locating and Editing Factual Associations in GPT*. Advances in Neural Information Processing Systems 35 (NeurIPS 2022). URL: https://proceedings.neurips.cc/paper_files/paper/2022/hash/6f1d43d5a82a37e89b0665b33bf3a182-Abstract-Conference.html.
- [SelfCheckGPT] Potsawee Manakul, Adian Liusie, and Mark J. F. Gales. 2023. *SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models*. Proceedings of EMNLP 2023, pages 9004-9017. DOI: 10.18653/v1/2023.emnlp-main.557. URL: https://aclanthology.org/2023.emnlp-main.557/.
- [TransformerCircuits] Nelson Elhage, Neel Nanda, Catherine Olsson, Tom Henighan, Nicholas Joseph, Ben Mann, Amanda Askell, Yuntao Bai, and others. 2021. *A Mathematical Framework for Transformer Circuits*. Transformer Circuits Thread. URL: https://transformer-circuits.pub/2021/framework/index.html.
- [TruthfulQA] Stephanie Lin, Jacob Hilton, and Owain Evans. 2022. *TruthfulQA: Measuring How Models Mimic Human Falsehoods*. Proceedings of ACL 2022, pages 3214-3252. DOI: 10.18653/v1/2022.acl-long.229. URL: https://aclanthology.org/2022.acl-long.229/.

## Appendix A. Registry Workflow

The registry workflow is designed to keep admitted examples, validation status, and tracing status in one canonical state file: `outputs/examples_registry.csv`.

The high-level lifecycle is:

1. Explore candidates from accepted source material.
2. Admit only examples that pass pre-registry checks.
3. Run token-span feasibility.
4. Author a minimal corrupted prompt candidate.
5. Run pair validation.
6. Promote only validated pairs to tracing.
7. Run tracing stages in order.
8. Mark completed examples with final tracing status.

Important final statuses include:

- `ready_for_validation`: authored row selected for validation.
- `parked`: deferred but potentially useful row.
- `processed_reject`: failed row that should not be reused casually.
- `pilot_complete`: completed pilot example.

## Appendix B. Excluded Examples

| Example | Status | Reason | Revisit later? |
| --- | --- | --- | --- |
| `51` | Failed | Pair validation failed. The clean run did not provide a clean validated setup for tracing, and the corrupted prompt did not produce a sufficiently clean hallucination-to-truth flip for the pilot. | Low priority. Revisit only if prompt validation settings or reproduction criteria change. |
| `3573` | Failed | Pair validation failed. The clean run did not reproduce the target date hallucination, and the corrupted run did not flip cleanly to the intended day-only correction. | Low priority for current pilot. Revisit only if date-target prompt design is revised. |
| `93` | Parked | Earlier review parked it rather than moving it through the full validated tracing workflow. It involved a date/timeline correction target that remains unvalidated for tracing. | Possible later, after the current validated set is expanded. |
| `597` | Parked | Earlier review parked it rather than moving it through the full validated tracing workflow. It involved a release-timing correction target that remains unvalidated for tracing. | Possible later, after the current validated set is expanded. |
| `2793` | Parked | Correction target was weak, so the clean/corrupted contrast was not strong enough for a reliable tracing pilot. | Low priority unless a stronger verified correction target is found. |
| `2265` | Ambiguous | Token mapping was ambiguous, making the hallucinated span unsuitable for the current token-level tracing workflow. | Revisit only if the workflow adds a split-token or ambiguous-span policy. |
| `2781` | Ambiguous | Token mapping was ambiguous, making the hallucinated span unsuitable for the current token-level tracing workflow. | Revisit only if the workflow adds a split-token or ambiguous-span policy. |

These examples are not counted as completed tracing evidence.

## Appendix C. Run Artifact Table

For example `813`, the saved run artifacts are:

| Stage | Run folder |
| --- | --- |
| Pair validation | `outputs/runs/20260425_060337_pair_validation_813/` |
| Forward pass | `outputs/runs/20260425_064458_forward_pass_813/` |
| Layer patching | `outputs/runs/20260425_070723_layer_patching_813/` |
| Head patching | `outputs/runs/20260425_073014_head_patching_813/` |
| Head ablation | `outputs/runs/20260425_075129_head_ablation_813/` |

Example `369` was completed before the run-folder refactor and is summarized in `docs/pilot_mechanistic_findings_369.md`.

## Appendix D. Prompt Construction Details

Each completed example uses:

- a clean input text for validation,
- a verified ground-truth target,
- a hallucinated substring,
- a corrupted prompt candidate,
- an edit class,
- an edit delta text,
- a minimality rationale.

The corrupted prompt is intended to be a small factuality-oriented intervention, not a wholesale rewrite of the task. This is important because large prompt changes would make the clean/corrupted comparison harder to interpret.

## Appendix E. Per-Example Evidence Table

| Example | Hallucination / correction target | Validation outcome | Divergence token | Top restoring layers | Top restoring heads | Best ablation result | Conservative interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `369` | Hallucinated full film title: `1986 John Hughes film "Pretty in Pink"`; correction target: `1986 John Hughes film`. | Validated. Clean run reproduced the target hallucination; corrupted run flipped to the verified truth without retaining the hallucinated substring. Full tracing completed. | Output-relative index `22`; hallucinated token `"` (id `376`); verified-truth token `,` (id `29892`). | `L30` (`16.460938`), `L29` (`16.390625`), `L23` (`15.804688`). | `L30H26` (`0.507812`), `L23H3` (`0.453125`), `L23H10` (`0.250000`), `L29H26` (`0.234375`), `L29H5` (`0.187500`). | Best single head: `L23H3` (`1.757812`). Best multi-head: `pair_L30H26_L23H3` (`3.046875`). | Strong pilot evidence that this example has causal restoration signal in late layers, especially `L29-L30`, with a stronger ablation effect than example `813`. Head candidates are example-specific. |
| `813` | Hallucinated charge: `10 counts of fraud`; correction target: `two counts of offering a false instrument for filing in the first degree`. | Validated. Clean run reproduced the target hallucination; corrupted run flipped to the verified truth without retaining the hallucinated substring. Full tracing completed. | Output-relative index `16`; hallucinated divergence token is a tokenizer boundary / whitespace-like token id `29871`; verified-truth token `two` (id `1023`). This tokenization detail should be interpreted carefully. | `L30` (`8.250000`), `L29` (`8.203125`), `L31` (`7.875000`). | `L29H5` (`0.554688`), `L29H21` (`0.140625`), `L31H4` (`0.085938`), `L31H31` (`0.062500`), `L30H31` (`0.054688`). | Best single head: `L29H5` (`0.257812`). Best multi-head: `top3_heads` (`0.179688`). | Strongest signal is again late-layer restoration around `L29-L30`, but ablation effects are smaller and the strongest head differs from `369`. This supports follow-up work, not a stable circuit claim. |

Future completed examples should be appended to this table and given their own Results subsection.

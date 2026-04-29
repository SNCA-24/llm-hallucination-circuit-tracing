# **Updated PRD — Professor-Aligned Version**

## **Title**

**Tracing Neural Circuits of LLM Hallucinations via Clean–Corrupted Prompt Pairs and Token-Level Causal Analysis**

## **1\. Document Purpose**

This PRD defines a project plan that is tightly aligned with the professor’s stated research goal and required experimental methodology. The project’s primary aim is to identify the internal model circuits — specifically layers, attention heads, and, where relevant, MLP components — that cause a language model to produce a hallucinated token. The core required method is to compare a hallucination-inducing run against a minimally edited corrective run and trace the internal computational differences at the exact hallucinated token position.

This PRD intentionally avoids expanding the project into a broad hallucination detector, safety filter, or intervention system. Those are out of scope unless the professor explicitly approves them after the main circuit-tracing objective is complete. That boundary is necessary to stay aligned with the professor’s objective.

This PRD assumes that no currently available public dataset fully satisfies the full clean/corrupted mechanistic tracing protocol out of the box. Accordingly, the project is defined around a **derived tracing subset** built from the strongest available base dataset, rather than assuming that a benchmark already ships professor-ready paired examples. Dataset choice is therefore judged primarily by **span precision, replayability, open-model compatibility, token/logit accessibility, and interpretability tooling fit**, not by benchmark size or popularity alone.

---

## **2\. Primary Objective**

Identify the specific internal model circuits responsible for causing a model to hallucinate, by isolating one hallucination type at a time and comparing internal activations between:

* a **clean run**: the original prompt that produces the hallucinated answer  
* a **corrupted run**: a minimally modified prompt that causes the same model to produce the correct answer

The analysis must be centered on the **exact hallucinated token** and must aim to localize the responsible computation to specific layers and attention heads, with optional refinement to MLP components if needed.

The paired examples used for this objective may be **constructed from a public base dataset** rather than assumed to exist natively in that dataset.

---

## **3\. Core Research Questions**

### **RQ1**

For a single hallucination type, which specific layers and attention heads most strongly contribute to the production of the hallucinated token?

### **RQ2**

When a minimal prompt edit flips the model from a hallucinated answer to a correct answer, which internal activations change in a causally meaningful way at the first divergent token?

### **RQ3**

After one hallucination type is successfully traced, does a second hallucination type rely on the same circuit, a partially overlapping circuit, or a different circuit?

These questions directly reflect the professor’s stated interest in whether different hallucination types are driven by different internal circuits.

---

## **4\. Non-Negotiable Alignment Rules**

The following are mandatory and cannot be relaxed without explicitly changing the project definition.

### **4.1 Single hallucination type first**

The project must begin with **one** hallucination type only. It must not begin with a broad taxonomy across many modes. Suitable first targets include a narrow type such as number hallucinations, date hallucinations, or a tightly defined entity hallucination type.

### **4.2 Clean–corrupted prompt pairs are the central unit of analysis**

The project must use paired examples in which:

* the original prompt still produces the hallucinated answer  
* a minimal prompt modification flips the output to the correct answer

Broader context perturbation regimes are not the main causal method in this PRD. They may be used later only as supporting analysis, not as the primary experimental design.

### **4.3 Exact token-level localization is mandatory**

The project must identify the exact hallucinated span in characters and map it to the exact token indices under the target model tokenizer. Sentence-level labeling is not sufficient for this project.

### **4.4 First divergent hallucinated token is the primary readout**

For each pair, the main analysis target is the **first token** at which the hallucinated path diverges from the corrected path. This is the token for logit comparison, activation caching, patching, and circuit attribution.

### **4.5 Specific layer/head localization is a required deliverable**

The project is not complete if it only produces aggregate mechanistic signatures. It must identify specific high-impact layers and attention heads, and show causal evidence for their role.

---

## **5\. Explicit Decision Gates**

To avoid hidden assumptions, the following fields remain open until locked.

### **Gate A — First hallucination type**

One and only one initial hallucination type must be locked before running the main experiment.

Allowed examples:

* number hallucination  
* date hallucination  
* short entity-name hallucination

Preferred choice from a tractability standpoint: **number or date hallucination**, because the span is shorter, verification is easier, and first-token divergence is cleaner. This is a practical recommendation, not an assumption.

### **Gate B — Target model/checkpoint**

 The target model must be:

* open-weight  
* runnable within the project compute budget  
* compatible with token-level logit extraction and activation hooks  
* compatible with the tokenizer used for span-to-token mapping  
* available in, or reproducible from, the chosen primary base dataset

**Default model scope for this project:**

* **Core phases (Phases 0–6): 7B open-weight models only**  
* **Later expansion / comparison phase: 13B models only if the 7B pipeline is already stable and resource-feasible**  
* **Models larger than 13B are out of scope for this project unless explicitly approved later**

**Default preference order:**

1. supported **7B** model families already available in the primary dataset pipeline  
2. supported **13B** variants only after the 7B workflow is validated  
3. larger models are excluded from the default plan because they add unnecessary compute and iteration complexity relative to the project’s current resource constraints  
   

### **Gate C — Dataset source**

The project will use a **primary base dataset** and may optionally use **auxiliary datasets**.

**Default primary base dataset:** RAGTruth\_Xtended-derived subset.

**Dataset ranking rule for this project:**

1. exact character-span availability  
2. reliable token mapping under the target tokenizer  
3. open-model compatibility  
4. logits / reproducible hidden-state access  
5. feasible path to constructing valid clean/corrupted pairs

**Auxiliary datasets are allowed only for support roles**, such as:

* edit-template inspiration,  
* secondary validation,  
* later generalization checks.

No auxiliary dataset may replace the primary base unless it improves the above criteria **for the professor’s tracing protocol**, not merely for generic hallucination evaluation.

### **Gate D — Allowed prompt edits for corrupted prompts**

Before pair construction begins, the project must lock what counts as an acceptable “minimal change.”

Allowed edit classes should be restricted to one or more of:

* a short disambiguating clause  
* one added supporting evidence sentence  
* a small clarification phrase  
* a format-preserving rewrite that does not change task intent

This must be fixed before dataset construction to avoid ad hoc edits later.

### **Gate E — Dataset continuation threshold**

Before committing to the main experiment, the project must run a small feasibility pilot on the chosen base dataset. The base dataset is retained only if the pilot yields a sufficient number of examples that simultaneously satisfy:

* exact span-to-token alignment,  
* reproducible clean hallucination behavior or high-fidelity teacher-forced scoring,  
* minimally edited corrected prompts,  
* clear first divergent token,  
* acceptable replay quality.

If the pilot fails, the project must pivot early to a smaller custom micro-benchmark rather than forcing weak examples into the tracing pipeline.

---

## **6\. In-Scope vs Out-of-Scope**

### **In scope**

* one hallucination type at a time  
* token-level span mapping  
* clean/corrupted pair construction  
* exact token logit comparison  
* activation caching at relevant layers  
* causal tracing via activation patching  
* localization of specific layers and heads  
* minimal ablation/verification of implicated components  
* optional second hallucination type only after the first one succeeds  
* construction of a **derived professor-aligned tracing subset** from a public base dataset

### **Out of scope**

* broad hallucination taxonomies as the main project  
* safety filters  
* operational gating policies  
* Answer/Re-retrieve/Abstain systems  
* calibration benchmarks  
* correction systems or steering vectors  
* generic sentence-level hallucination detection  
* treating a public hallucination benchmark as mechanistic-tracing-ready without pair-validity auditing

These were deliberately excluded because they shift the project away from the professor’s stated objective.

---

## **7\. Success Definition**

The project is successful only if all of the following are achieved for at least one hallucination type:

1. The chosen base dataset successfully passes the feasibility audit and yields a valid derived tracing subset.  
2. A curated, audited, and provenance-tracked set of clean/corrupted prompt pairs exists for a single hallucination type.  
3. Each example has exact character-level hallucination spans and exact token-level mapping under the target tokenizer.  
4. The first divergent hallucinated token is identified for each pair.  
5. The project measures token-level logit differences between hallucinated and corrected runs.  
6. Layer-wise causal tracing identifies a small set of candidate high-impact layers.  
7. Head-level tracing within those layers identifies specific attention heads associated with the hallucinated token.  
8. At least one causal verification step shows that patching or ablating those components changes the hallucination behavior in the expected direction.  
9. The results are reported conservatively, distinguishing causal findings from merely correlational observations.

If the project stops at “mechanistic patterns” without localizing specific heads/layers, it does **not** meet the professor’s core objective.

---

## **8\. End-to-End Experimental Plan**

## **Phase 0 — Feasibility Lock and Experimental Freeze**

### **Goal**

Lock the project configuration before large-scale work begins.

### **Required outputs**

* chosen hallucination type  
* chosen model/checkpoint  
* chosen dataset source  
* locked corrupted-prompt edit policy  
* locked generation settings  
* locked tokenizer  
* locked evaluation template for pair validation  
* dataset feasibility audit  
* pilot pair-yield report  
* replay-quality summary on pilot examples  
* primary/auxiliary dataset role assignment  
* locked model-size scope (**7B core / 13B later only if justified**)

### **Rules**

No mechanistic experiment begins before these are frozen.

### **Deliverable**

`docs/experiment_freeze.md`

`docs/dataset_feasibility_audit.md`

`docs/pilot_pair_yield_report.md`

---

## **Phase 1 — Data Curation for One Hallucination Type**

### **Goal**

Produce a high-purity subset of examples suitable for token-level tracing. Phase 1 should begin from the **primary base dataset**, but must produce a **smaller high-purity derived subset** rather than attempting to use the raw benchmark wholesale.

### **Required inclusion criteria**

Each retained example must have:

* original prompt  
* model output containing the hallucination  
* exact hallucinated text span in characters  
* exact token mapping under the target tokenizer  
* a correct target value or correct target string that can be verified  
* a hallucination that is short and localized enough to identify a clear first divergent token  
* example comes from the chosen target model family  
* example belongs to the chosen primary language partition  
* example has one short dominant hallucinated span or one clearly dominant first hallucinated token  
* example has sufficient evidence to verify the correct target string  
* example is compatible with the chosen prompt template and tokenizer

### **Exclusion criteria**

Reject any example with:

* ambiguous correctness  
* diffuse multi-sentence hallucination  
* no clear first divergent token  
* tokenizer alignment ambiguity  
* unrepeatable formatting  
* unresolvable mismatch between dataset model and target model  
* prompt that cannot be minimally edited without changing task intent  
* multi-language or cross-model mixing in the core tracing subset  
* examples whose hallucination type cannot be cleanly assigned to the chosen first type  
* examples with multiple competing hallucinated spans that obscure the first divergence  
* examples that require large semantic rewrites to correct

### **Deliverables**

* `data/curated_examples.csv`  
* `docs/selection_policy.md`  
* `docs/example_review_notes.md`

### **Mandatory note**

- The goal here is not dataset breadth. It is **purity and traceability**.  
- If the primary base is RAGTruth\_Xtended, the tracing subset should be aggressively filtered rather than broadly reused.

---

## **Phase 2 — Clean/Corrupted Pair Construction and Validation**

### **Goal**

Turn curated examples into valid paired examples for causal tracing.

### **Definition of valid pair**

A pair is valid only if:

* the clean prompt still produces the hallucinated answer under locked settings  
* the corrupted prompt differs minimally from the clean prompt  
* the corrupted prompt produces the correct answer  
* the main task and semantic intent remain unchanged  
* the hallucinated and corrected outputs can be aligned at the first divergent token

### **Pair Acceptance Requirements** 

* each pair must store the exact **edit class** used  
* each pair must store the exact **edited text delta**  
* each pair must store a short **why-this-is-minimal** note  
* each pair must be reviewed for **semantic equivalence of task intent**  
* each pair must record whether the correction came from:  
  * manual edit,  
  * template-guided edit,  
  * auxiliary dataset-inspired edit

### **Pair construction workflow**

For each curated example:

1. run the original prompt under fixed settings  
2. confirm hallucination reproduction or high-fidelity teacher-forced scoring  
3. propose one minimal corrupted prompt edit from the locked edit classes  
4. run the modified prompt under the same settings  
5. retain only pairs that flip from hallucinated to correct

Auxiliary resources such as FAVA may be used only as **edit-template inspiration** for how minimal corrective edits can be structured. They are not the primary mechanistic dataset and must not be mixed into the core tracing claims unless separately audited under the same protocol.

### **Deliverables**

* `data/pairs_clean_corrupted.jsonl`  
* `docs/pair_construction_protocol.md`  
* `docs/pair_acceptance_criteria.md`

### **Failure rule**

If the valid-pair yield is too low, the project must not broaden the hallucination type or relax pair standards. It must instead pivot to a smaller custom micro-benchmark or a tighter subset.

---

## **Phase 3 — Replay, Token Alignment, and Exact Readout Position**

### **Goal**

Ensure the model-side analysis is performed on a precisely defined token position.

### **Required computations per pair**

* tokenize clean and corrupted prompts with the locked tokenizer  
* map character-level hallucinated span to token-level span  
* identify the first hallucinated token  
* identify the first divergent token between clean and corrected generations  
* compute token-level logprobs/logits at that position  
* Required stored metrics   
  * mean token logprob over answer tokens  
  * token-level agreement at the first divergent position  
  * replay mode  
  * replay quality flag

### **Replay policy**

Two replay modes are allowed:

#### **Mode A — Exact generation replay**

Preferred when the chosen checkpoint and generation setup reproduce the dataset behavior.

#### **Mode B — Teacher-forced replay**

Allowed when exact replay is unstable, but only if the answer tokens can still be scored under the chosen checkpoint and the target token positions remain valid for analysis.

Teacher forcing supports the tracing process, but it does not remove the need for valid clean/corrupted pairs.

**Replay-quality claim tiers**  
 Mechanistic results must be reported separately for:

* the **full retained subset**, and  
* the **high-replay subset**

Stronger mechanistic claims should be anchored primarily in the high-replay subset.

### **Deliverables**

* `results/replay_stats.parquet`  
* `results/token_maps.parquet`  
* `docs/replay_quality_rules.md`

**Note:** 

A high-replay subset will be defined using locked replay-quality thresholds in `docs/replay_quality_rules.md`

---

## **Phase 4 — Layer-Level Causal Tracing**

### **Goal**

Find which layers matter most for the hallucinated token.

### **Main readout**

For each pair, define a token-level score such as:

* hallucinated-token logit minus corrected-token logit, or  
* corrected-token restoration score at the first divergent position

### **Required procedure**

1. cache activations for the clean run  
2. cache activations for the corrupted run  
3. perform layer-wise activation patching  
4. patch corrected activations into the clean run, one layer at a time  
5. measure which layer most suppresses the hallucinated token or restores the corrected token  
6. rank layers by causal effect size

### **Required output**

A small set of high-impact layers for the chosen hallucination type.

### **Deliverables**

* layer ranking plots  
* per-example causal traces  
* aggregated layer importance summary

This phase must directly support the professor’s “which layers are causing the hallucination?” objective.

**Note**: Layer rankings must be computed on a dataset-homogeneous tracing subset and must not mix primary and auxiliary datasets in the same causal ranking.

---

## **Phase 5 — Head-Level Localization Within High-Impact Layers**

### **Goal**

Refine the layer-level result to specific attention heads.

### **Required procedure**

For each high-impact layer:

1. patch head outputs individually  
2. measure change in hallucinated-token vs corrected-token score  
3. rank heads by causal effect  
4. identify a minimal set of strongest candidate heads

### **Optional refinement**

If results indicate strong MLP contribution, run a limited analogous analysis on MLP blocks only after the head analysis is complete. 

### **Required output**

A ranked list of specific heads, with effect sizes and consistency across examples.

### **Deliverables**

* `results/head_importance.csv`  
* head attribution plots  
* example-level head-effect traces

This phase is required because the professor explicitly wants localization to specific layers and attention heads.

**Note**: If the first hallucination type is numerical or date-like, MLP contribution may be probed earlier as a parallel secondary analysis, but attention-head localization remains a required deliverable.

---

## **Phase 6 — Causal Verification of the Identified Circuit**

### **Goal**

Show that the identified components are not merely correlated but causally relevant.

### **Accepted causal tests**

At least one of the following is required:

#### **Test A — Restorative patching**

Patch corrected activations into the clean run and show predictable restoration toward the correct token.

#### **Test B — Destructive ablation**

Ablate the identified layer/head components in the hallucinating run and show that hallucination strength decreases or the output shifts away from the hallucinated token.

#### **Test C — Minimal circuit patching**

Patch only the identified candidate components rather than whole-layer activations and show that they explain a meaningful fraction of the effect.

### **Not sufficient on their own**

* attention summaries  
* CAM-like aggregate metrics  
* broad perturbation deltas  
* sentence-level behavioral changes

Those may support interpretation, but they do not replace token-level causal verification for this project.

### **Deliverables**

* causal verification table  
* before/after logit-difference plots  
* concise boundary statement separating causal findings from descriptive patterns

**Note** : Causal verification claims must identify the exact subset on which they hold: full subset, high-replay subset, or manually verified core subset.

---

## **Phase 7 — Cross-Type Comparison Only After First Success**

### **Goal**

Answer the professor’s broader question about whether different hallucination types use different circuits.

### **Entry condition**

Phase 7 begins only if Phases 1–6 are successful for the first hallucination type.

### **Procedure**

Repeat the full pipeline on exactly one additional hallucination type:

* same **7B model family** if possible  
* 13B comparison is optional and allowed only after the 7B tracing pipeline is stable, reproducible, and resource-feasible on Colab  
* same tracing methodology  
* same reporting structure

### **Comparison output**

Compare:

* top layers  
* top heads  
* sign and magnitude of causal effects  
* consistency of implicated heads across examples

### **Success interpretation**

* strong overlap suggests shared circuit machinery  
* weak overlap suggests type-specific circuits  
* partial overlap suggests shared upstream processing with type-specific downstream specialization

This sequencing is important: the project must not begin with multiple types.

**Note**: The second hallucination type may come from the same primary base dataset or from a secondary validation dataset, but the tracing pipeline must remain identical and the dataset switch must be explicitly disclosed.

---

## **9\. Data and Annotation Requirements**

For every retained example, the project must store:

* example ID  
* hallucination type  
* clean prompt  
* corrupted prompt  
* clean output  
* corrected output  
* exact hallucinated character span  
* exact hallucinated token span  
* first hallucinated token index  
* first divergent token index  
* correct target token/string  
* model/checkpoint identifier  
* tokenizer identifier  
* generation settings  
* reproduction status  
* reviewer notes  
* `base_dataset_name`  
* `base_dataset_split`  
* `dataset_role` (primary / auxiliary)  
* `edit_class`  
* `edit_delta_text`  
* `pair_construction_source` (manual / template-guided / auxiliary-inspired)  
* `pair_validity_status`  
* `replay_mode`  
* `replay_quality_flag`  
* `replay_quality_metrics`  
* `subset_membership` (full / high-replay / manually verified core)  
* `keep_reason`

This is the minimum data structure needed to make the tracing reproducible and auditable.

---

## **10\. Logging and Reproducibility Rules**

### **Mandatory logging**

Every run must record:

* model checkpoint  
* tokenizer version  
* prompt template  
* generation settings  
* pair ID  
* token map  
* target token position  
* replay mode  
* patching configuration  
* metric definition

### **Mandatory reproducibility rules**

* no hidden manual edits after pair acceptance  
* no changing generation settings mid-analysis  
* no mixing tokenizers  
* no changing corruption policy after pair construction starts  
* no mechanistic claim from an example that lacks exact token mapping

### **Compute rule**

Store summary outputs and targeted activation slices needed for the analysis, not uncontrolled tensor dumps.

**Dataset rules**

* no mixing primary and auxiliary datasets inside a single core causal ranking without explicit labeling  
* no mechanistic claim from low-replay examples without marking it as exploratory  
* every pair must preserve edit provenance  
* every run must log dataset source and subset membership  
* Selection, thresholding, and any later comparison logic must not leak information across manually defined experiment subsets.

---

## **11\. Claim Standards**

### **Allowed claims**

The project may claim:

* specific layers and heads are implicated in the hallucinated token  
* those components show causal influence under patching/ablation  
* one hallucination type appears to rely on a particular circuit pattern  
* a second hallucination type shows overlap or divergence relative to the first

### **Not allowed unless directly supported**

The project may not claim:

* a universal hallucination mechanism across all hallucination types  
* broad RAG safety conclusions  
* production detection utility  
* intervention effectiveness beyond the traced examples  
* causality from descriptive metrics alone  
* claims that a public benchmark natively validates the professor’s method without derived pair construction  
* claims that results generalize beyond the primary dataset/model setting unless replicated

This section is necessary to keep the write-up scientifically defensible.

---

## **12\. Main Risks and Required Fallbacks**

### **Risk 1 — Existing datasets do not provide valid clean/corrupted pairs**

**Fallback:** build a small custom micro-benchmark around one model and one hallucination type rather than forcing weak pairs from a public benchmark.

### **Risk 2 — Exact generation replay is unstable**

**Fallback:** use teacher-forced replay for scoring and activation extraction, but keep the clean/corrupted pair requirement intact.

### **Risk 3 — Span-to-token alignment is messy**

**Fallback:** reject those examples. Do not downgrade to sentence-level analysis.

### **Risk 4 — Head-level attribution is noisy**

**Fallback:** first identify robust high-impact layers, then narrow to heads only within those layers, using repeated examples and conservative ranking.

### **Risk 5 — The first chosen hallucination type is too diffuse**

**Fallback:** switch to a shorter and cleaner hallucination type, such as number/date hallucinations.

### **Risk 6 — Patching shows broad layer effects but not crisp head effects**

**Fallback:** report reliable layer-level findings and continue head refinement only where supported, but do not replace the core objective with aggregate mechanistic signatures.

### **Risk 7 — No public dataset fully satisfies the protocol**

**Fallback:** treat the public dataset as a base substrate only and explicitly build a derived tracing subset.

### **Risk 8 — Pair yield is too low despite good spans**

**Fallback:** narrow the hallucination type further before changing datasets.

### **Risk 9 — Benchmark attractiveness causes wrong dataset choice**

**Fallback:** prioritize replayability, tool compatibility, and pair feasibility over benchmark novelty or size.

---

## **13\. Deliverables**

### **Required deliverables**

* professor-aligned final PRD  
* curated single-type dataset subset  
* validated clean/corrupted pair set  
* token span mapping pipeline  
* replay statistics and target token maps  
* layer-level causal tracing results  
* head-level localization results  
* causal verification results  
* dataset feasibility audit  
* pair-yield and replay-quality audit  
* dataset-role appendix documenting primary vs auxiliary usage  
* final report answering:  
  * which layers/heads caused hallucination type 1  
  * whether hallucination type 2 shares or differs from that circuit, if Phase 7 is reached

### **Optional deliverables**

Only after core success:

* second hallucination type comparison  
* limited MLP refinement  
* compact demo notebook for one traced example

---

## **14\. Anti-Scope-Creep Rules**

* Start with one hallucination type only.  
* One model/checkpoint only in the first pass.  
* No moving beyond **7B models** in the core project phases; **13B** is allowed only as a later, conditional extension after the 7B pipeline is stable  
* Clean/corrupted prompt pairs are mandatory.  
* Exact token-level analysis is mandatory.  
* First divergent token is the main readout.  
* Specific layers and attention heads are required deliverables.  
* No safety filter, no gating system, no correction policy, no steering phase unless explicitly added later as a separate project.  
* No sentence-level fallback.  
* No broad taxonomy-first exploration before a valid tracing subset exists.  
* No assuming that a public dataset already provides valid clean/corrupted pairs unless that has been explicitly audited.  
* No switching the primary dataset solely because another dataset looks richer on one axis

---

## **15\. One-Page Execution Checklist**

The project can start only if:

* feasibility pilot passes  
* pilot pair-yield is acceptable  
* replay-quality on pilot is acceptable  
* primary vs auxiliary dataset roles are fixed  
* hallucination type is locked  
* model/checkpoint is locked  
* dataset source is locked  
* allowed corrupted-prompt edits are locked  
* tokenization pipeline is locked  
* model-size scope is locked (**7B core; 13B only as later optional extension**)

A pair can be admitted only if:

* clean prompt hallucinates  
* corrupted prompt is minimal  
* corrupted prompt yields the correct answer  
* exact token alignment exists  
* first divergent token is clear

A mechanistic claim can be made only if:

* the claim is tied to a specific token position  
* a specific layer or head is identified  
* a causal patching or ablation result supports the claim

A second hallucination type can be studied only if:

* the first hallucination type has already produced stable circuit-localization results

---

## **16\. Final Alignment Statement**

This PRD is aligned to the professor’s project definition because it treats the project as a **circuit-localization problem**, not as a general hallucination-analysis or safety-monitoring problem. It begins with one hallucination type, requires clean/corrupted prompt pairs, centers the analysis on the exact hallucinated token, and makes localization of specific layers and attention heads the primary deliverable. Those are the key methodological requirements stated by the professor. This alignment is maintained not by assuming a perfect public benchmark exists, but by explicitly building a professor-aligned derived tracing subset on top of the strongest available base dataset.

## **What still needs confirmation from you before this becomes execution-ready**

I did not assume these:

1. the first hallucination type to lock  
2. the exact **7B target model/checkpoint** for the core project, and whether a **13B follow-up** will be considered later  
3. the exact dataset starting point  
4. which prompt edits are allowed for the corrupted prompt
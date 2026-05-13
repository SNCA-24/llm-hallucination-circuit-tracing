# Third-Party Notices

This repository's [LICENSE](LICENSE) applies to original project code, scripts, documentation, and project scaffolding unless a file or directory states otherwise.

Third-party datasets, model checkpoints, model weights, hosted artifacts, and external libraries remain governed by their own licenses and terms. Nothing in this repository relicenses those upstream materials under MIT.

Unless otherwise noted below, this repository includes only project code, configuration, lightweight metadata, or references needed to work with the external resource. Large upstream datasets and model artifacts are intentionally not committed here.

## RAGTruth

- Name: RAGTruth: A Hallucination Corpus for Developing Trustworthy Retrieval-Augmented Language Models
- Source URLs:
  - Paper reference used in this repo: https://aclanthology.org/2024.acl-long.585/
  - Upstream repository: https://github.com/ParticleMedia/RAGTruth
- Terms note: RAGTruth remains governed by its upstream license and terms. These project notices do not modify or replace those terms.
- Included here: No full upstream dataset checkout is included. This repository contains project scripts, templates, loaders, and lightweight metadata that reference or expect separately downloaded RAGTruth resources.

## RAGTruth_Xtended

- Name: RAGTruth_Xtended
- Source URLs:
  - Paper reference used in this repo: https://arxiv.org/abs/2507.20836
  - Upstream repository: https://github.com/jakobsnl/RAGTruth_Xtended
- Terms note: RAGTruth_Xtended remains governed by its upstream license and terms. These project notices do not modify or replace those terms.
- Included here: No full upstream dataset checkout is included. This repository contains project code that can interoperate with a separately downloaded RAGTruth_Xtended checkout.

## Llama-2 / Llama-2-7B-Chat

- Name: Llama 2 / Llama-2-7B-Chat
- Source URLs:
  - Paper reference used in this repo: https://arxiv.org/abs/2307.09288
  - Official model access and license page: https://ai.meta.com/resources/models-and-libraries/llama-downloads/
- Terms note: Llama 2 model weights, tokenizers, and related artifacts remain governed by the Meta Llama 2 license and any applicable access or hosting terms. This repository does not relicense those artifacts under MIT.
- Included here: No model checkpoints, tokenizer files, or weight files are committed. The repository includes scripts and configuration that reference Llama 2 model identifiers, including Hugging Face-hosted variants such as `NousResearch/Llama-2-7b-chat-hf`, which must be obtained separately under their applicable terms.

## Hugging Face Transformers / PyTorch

- Name: Hugging Face Transformers
- Source URL: https://github.com/huggingface/transformers
- Terms note: The `transformers` library remains governed by its upstream license and terms. At the time of writing, its upstream repository identifies the project as Apache-2.0 licensed.
- Included here: No vendored copy is included. This repository references `transformers` as an external dependency in `requirements.txt`.

- Name: PyTorch
- Source URL: https://github.com/pytorch/pytorch
- Terms note: PyTorch remains governed by its upstream license and terms. At the time of writing, its upstream repository describes PyTorch as BSD-style licensed.
- Included here: No vendored copy is included. This repository references `torch` as an external dependency in `requirements.txt`.

## Other External Resources

Additional third-party packages or resources referenced by this repository, including dependencies listed in `requirements.txt` and separately downloaded runtime artifacts, remain subject to their own licenses and terms.

# M1 evidence review

**Status: completed development-stage semantic spot-check; model judgment.**

The frozen [dossier](../data/m1/dossier.json) contains six principal public sources, an official English companion for the Vietnamese source, and 16 typed claims. Its evidence cutoff is **2026-09-14 23:56:51 UTC** (2026-09-15 in the project's Europe/Berlin timezone). The [case](../data/m1/case.json) and [disruption](../data/m1/disruption.json) are separately labeled scenario inputs. File digests are in [SHA256SUMS](../data/m1/SHA256SUMS).

## What was checked

A Codex development evidence subagent opened the cited public source pages and PDF text through the browsing tool and compared important claim wording against the passages below. This work prepared the inputs for application research workers. It is **not** a research-worker interaction, independent expert validation, or verification of implementation.

| Claim | Primary source and precise locator | Semantic spot-check result |
|---|---|---|
| `C_JP_CO_CREATION` | [Japan MOFA summit account](https://www.mofa.go.jp/a_o/rp/pageite_000001_00004.html), section 1(2)(ii), second bullet | Supported as a proposal. No funding or pilot consent inferred. |
| `C_ASEAN_GOVERNANCE` | [ASEAN Guide](https://asean.org/wp-content/uploads/2024/02/ASEAN-Guide-on-AI-Governance-and-Ethics_beautified_201223_v2.pdf#page=8), printed page 8, Introduction 1 and 2 | Scope, voluntary adoption and non-substitution of national requirements checked. |
| `C_ASEAN_GENAI` | [Expanded ASEAN Guide](https://asean.org/wp-content/uploads/2025/01/Expanded-ASEAN-Guide-on-AI-Governance-and-Ethics-Generative-AI.pdf#page=28), printed page 28, section 3.5, opening paragraphs and item (a) | Regional evaluation recommendation and acknowledged testing limitations both retained. |
| `C_TH_CAPACITY_POLICY` | [NECTEC policy announcement](https://www.nectec.or.th/en/about/news/cabinet-national-ai-strategy.html), opening paragraph and five-strategy list | Approval report and priorities checked; expected results excluded as achieved capacity. |
| `C_TH_LANGUAGE_CAPABILITY_REPORT` | [NECTEC Pathumma description](https://www.nectec.or.th/innovation/innovation-service/pathumma-llm.html), second substantive paragraph and first two feature bullets | Thai text supports the attributed institutional description. Performance was not tested. |
| `C_VN_STRATEGY`, `C_VN_LANGUAGE_MODELS` | [Vietnamese Government News](https://baochinhphu.vn/chien-luoc-quoc-gia-ve-tri-tue-nhan-tao-den-nam-2030-tam-nhin-den-nam-2045-102260828184636823.htm), lead; first two paragraphs under the first subheading; final paragraph under the second subheading | Approval report, foundations and language-model target checked against Vietnamese text and the [official English companion](https://en.baochinhphu.vn/govt-approves-national-ai-strategy-111260829094257423.htm). Targets remain aspirations. |

PDF locators use **one-based displayed/PDF page numbers**, not the browsing tool's zero-based internal page index. The reviewed PDF pages are predominantly text; no claims depend on interpreting an unseen table or image.

## Retrieval and preservation

The browsing tool supplied readable source text for all six principal sources. A separate direct HTTP retrieval read available bytes into memory solely to calculate SHA-256 hashes; full source documents were not stored. Five principal sources and the Vietnamese English companion returned HTTP 200. The MOFA direct request returned HTTP 403 at `2026-09-14T23:56:47.352418Z`; its earlier browsing retrieval succeeded, so its source hash is honestly recorded as unknown. No inaccessible text was reconstructed.

Each source record stores its publication date with available precision, retrieval time, URL, locator, short original paraphrase, language/translation status, and limits. The MOFA timestamp records the end of its browsing batch rather than an unavailable individual response time. The two ASEAN publication dates have month precision; their exact publication days were not established. Direct HTML byte hashes can change with navigation or surrounding page updates even when the cited passage is unchanged.

The Thai source paraphrase is a model translation. Vietnamese passages were checked in the original language and against Government News's English companion; the English article is an official companion account, not asserted to be a complete or certified translation of the signed Decision. The signed 2026 instrument itself was not reviewed.

The initial search also opened the [2021 Vietnamese decision metadata](https://chinhphu.vn/default.aspx?docid=202565&pageid=27160) and its linked scanned PDF, whose text extraction was unavailable. Neither supplies a dossier claim. Discovery then found the August 2026 official strategy account, which became the bounded case's Vietnamese policy source. The review does not establish the current legal effect or supersession relationship of these instruments.

## Epistemic boundaries

The claim ledger distinguishes documented fact, interpretation, assumption and unknown. “Documented fact” here includes the fact that a named institution published a proposal, target or capability description; it does not convert that description into independently verified achievement. `I_COOPERATION_DESIGN_SPACE` is an expressly labeled synthesis by the development model.

The two initial true values are modeling assumptions:

- `contribution_available`: an anonymous proposed contribution is available for conditional planning only; rights and suitability do not follow.
- `coordination_authorized`: drafting proposals, questions and criteria is within the case's preparatory boundary; it gives no authority to act for an institution or use its data.

`partner_consent`, `pooled_processing_permission`, `local_processing_permission`, `funding_confirmed` and `evaluation_capacity` remain `null`. Their unknown claims concern this dossier's bounded evidence, not universal statements that such resources or permissions do not exist. The fictional disruption changes only the contribution flag. No real withdrawal, refusal, event or held-out test is asserted.

No explicit contradiction was found in the selected passages. That finding is limited by the small, favorable-policy-heavy sample. Potential disagreements over control, workload, language priorities, benefit sharing and accountability require investigation; no national preferences or numerical utilities were fabricated. Architecture suitability and political feasibility remain questions for the worker cycle and ultimately affected people.

## Limits and next evidence

This is a purposive six-source dossier, not a comprehensive literature survey, policy currency audit, legal analysis or independent model benchmark. Thailand's policy announcement is an explicitly historical source; later changes were not exhaustively surveyed. No people were contacted, no private datasets were accessed and no models were downloaded. The browser retrievals and semantic comparison establish the recorded limited review; software source-ID checks establish only referential integrity.

Before any operational recommendation, obtain named partners' authorization, a specific contribution inventory and provenance, qualified advice on intended processing, realistic staffing/compute costs, and a jointly agreed evaluation plan. Preserve the frozen dossier for this demonstration; add new evidence under a new version for later work.

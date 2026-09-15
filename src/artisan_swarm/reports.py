"""Decision memo rendered from saved research artifacts, without new model calls."""
from __future__ import annotations


def decision_brief(view: dict) -> str:
    review, revision = view["review"], view["revision"]
    selected = view["selection"]["selected_id"]
    parents = [p for p in view["candidates"] if not p["parent_ids"]]
    child = revision["program"]
    lines = ["# M1 decision brief", "", f"**Run:** {view['manifest']['run_id']} · **Evidence cutoff:** {view['dossier']['evidence_cutoff']}", "",
             "## Decision question", "", view["case"].get("decision_question", view["case"]["description"]), "",
             "This is decision support for a proposed collaboration. The data loss is an explicit hypothetical development scenario; no institution's withdrawal or trilateral commitment is asserted.", "",
             "## Recommendation and confidence boundary", "",
             review["recommendation"], "",
             f"**Fresh model review:** {review['outcome']}. **Substantive repair judged by that model:** {review['substantive_repair']}. "
             "This is a model judgment under a small frozen dossier, not independent expert validation or political approval.", "",
             "## Three alternatives", "",
             "| Architecture | Proposal | Changed-case supported / conditional / blocked / inactive |", "|---|---|---|"]
    for parent in sorted(parents, key=lambda p: p["architecture"]):
        s = view["executions"]["changed"][parent["id"]]["summary"]
        counts = " / ".join(str(len(s[k])) for k in ("supported", "conditional", "blocked", "inactive"))
        lines.append(f"| {parent['architecture'].replace('_', ' ')} | {parent['title'].replace('|', '/')} (`{parent['id']}`) | {counts} |")
    lines += ["", "All three parent programs remain archived; selection allocated further investigation and did not rank national benefit.", "",
              "## What changed and why", "", f"Selected parent: `{selected}`. Descendant: `{child['id']}`.", "",
              view["selection"]["reason"], "", revision["change_summary"], "",
              "### Executed before / after", "", "| Program | Case | Supported | Conditional | Blocked | Inactive |", "|---|---|---|---|---|---|"]
    for candidate_id, phase in ((selected, "initial"), (selected, "changed"), (child["id"], "changed")):
        s = view["executions"][phase][candidate_id]["summary"]
        cells = [", ".join(s[k]) or "—" for k in ("supported", "conditional", "blocked", "inactive")]
        lines.append(f"| `{candidate_id}` | {phase} | " + " | ".join(cells) + " |")
    lines += ["", "Supported means recommended under the stated scenario assumptions; no action was implemented in the world. Action counts are software observations, not utility or proof of improvement.", "",
              "### Causal rationale (fresh model judgment)", ""] + ["- " + r for r in review["reasons"]]
    for title, items in (("New weaknesses introduced", revision["new_weaknesses"]),
                         ("Unresolved interests and dependencies", review["unresolved_interests"]),
                         ("Resource requirements", review["resource_requirements"]),
                         ("Next evidence to obtain", review["next_evidence"])):
        lines += ["", "## " + title, ""] + ["- " + item for item in items]
    lines += ["", "## Adaptation triggers", ""]
    triggers = list(dict.fromkeys(t for a in child["actions"] for t in a["reconsideration_triggers"]))
    lines += ["- " + t for t in triggers]
    lines += ["", "## Strongest objection", "", review["strongest_objection"], "",
              "## Evidence and epistemic limits", "",
              "Documented policy facts and interpretations below have locators in the frozen claim ledger. Scenario assumptions and unknown commitments remain separate; a valid ID alone does not verify support.", ""]
    for claim in view["dossier"]["claims"]:
        refs = []
        for source_id in claim["source_ids"]:
            source = next(s for s in view["dossier"]["sources"] if s["id"] == source_id)
            refs.append(f"[{source_id}]({source['url']})")
        lines.append(f"- **{claim['id']} ({claim['type']}):** {claim['text']} " + "; ".join(refs) + f" Locator: {claim['locator']}")
    lines += ["", "## Run resources and inspectable artifacts", "",
              "Application research uses gpt-6-astra with medium reasoning through the existing ChatGPT-authenticated Codex CLI. The six logical jobs are three isolated discoveries, cross-candidate criticism, targeted revision and a fresh review. Actual CLI invocation counts and observed tokens are in manifest.json and jobs/*/attempt-*.json. Monetary cost and exact provider HTTP request/retry counts are unknown.", "",
              "In this run directory: `candidates/`, `executions/initial/`, `executions/changed/`, `jobs/`, `criticism.json`, `selection.json`, `revision.json`, `semantic_diff.json`, `lineage.json`, `review.json`, `manifest.json`, and `replay.json`. Replay re-executes saved outputs with zero model calls.", "",
              "The evidence review is a limited model spot-check. M1 does not establish an interaction advantage, calibrated geopolitical fitness, practitioner acceptance or recursive engine improvement.", ""]
    return "\n".join(lines)

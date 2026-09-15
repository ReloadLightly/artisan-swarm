"use strict";

// Untrusted worker prose is always inserted as text. No HTML from artifacts runs.
const $ = (id) => document.getElementById(id);
const state = { view: null, selected: null, changed: false, scenario: null, loading: false };
const token = document.querySelector('meta[name="csrf-token"]').content;
const words = (value) => String(value ?? "").replaceAll("_", " ");
const text = (value) => typeof value === "string" ? value : JSON.stringify(value, null, 2);
const asList = (value) => Array.isArray(value) ? value : value && typeof value === "object" ? Object.values(value) : [];
const candidatesInOrder = () => asList(state.view.candidates).slice().sort((a, b) => Number(Boolean(a.parent_ids?.length)) - Number(Boolean(b.parent_ids?.length)));

function node(tag, className, content) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (content !== undefined && content !== null) element.textContent = String(content);
  return element;
}

function safeLink(label, url) {
  const link = node("a", "", label);
  try {
    const parsed = new URL(url);
    if (["https:", "http:"].includes(parsed.protocol)) {
      link.href = parsed.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
    }
  } catch (_) { /* Unresolvable artifact links remain plain text. */ }
  return link;
}

function inline(parent, source) {
  const value = String(source ?? "");
  const pattern = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*|`([^`]+)`/g;
  let last = 0;
  for (const match of value.matchAll(pattern)) {
    parent.append(document.createTextNode(value.slice(last, match.index)));
    parent.append(match[1] ? safeLink(match[1], match[2]) : node(match[3] ? "strong" : "code", "", match[3] || match[4]));
    last = match.index + match[0].length;
  }
  parent.append(document.createTextNode(value.slice(last)));
}

function markdown(container, content) {
  container.replaceChildren();
  if (!content) { container.append(node("p", "empty", "No decision brief has been produced for this run yet.")); return; }
  const lines = String(content).split("\n");
  let list = null;
  let code = null;
  let table = null;
  for (const line of lines) {
    if (line.startsWith("```")) {
      if (code) { code = null; } else { code = node("pre"); container.append(code); }
      list = null; table = null; continue;
    }
    if (code) { code.append(document.createTextNode(line + "\n")); continue; }
    if (!line.trim()) { list = null; table = null; continue; }
    if (/^\s*\|.*\|\s*$/.test(line)) {
      if (/^[\s|:\-]+$/.test(line)) continue;
      const first = !table;
      if (!table) { table = node("table"); const wrap = node("div", "table-scroll"); wrap.append(table); container.append(wrap); }
      const row = node("tr");
      for (const cell of line.trim().slice(1, -1).split("|")) { const element = node(first ? "th" : "td"); inline(element, cell.trim()); row.append(element); }
      table.append(row); list = null; continue;
    }
    table = null;
    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    const item = /^\s*(?:[-*]|\d+\.)\s+(.*)$/.exec(line);
    if (heading) { const element = node("h" + heading[1].length); inline(element, heading[2]); container.append(element); list = null; }
    else if (item) { if (!list) { list = node("ul"); container.append(list); } const element = node("li"); inline(element, item[1]); list.append(element); }
    else { const element = node("p"); inline(element, line); container.append(element); list = null; }
  }
}

function structured(value, depth = 0) {
  if (value === null || value === undefined) return node("p", "empty", "Not available in this run yet.");
  if (typeof value !== "object") { const element = node("p"); inline(element, value); return element; }
  if (depth > 5) return node("pre", "", text(value));
  if (Array.isArray(value)) {
    if (!value.length) return node("span", "micro", "None recorded");
    const wrap = node("div");
    for (const item of value) {
      const element = node("div", typeof item === "object" ? "field-object" : "field-value");
      element.append(structured(item, depth + 1)); wrap.append(element);
    }
    return wrap;
  }
  const wrap = node("div", "artifact-fields");
  for (const [key, item] of Object.entries(value)) {
    const field = node("div", "field");
    field.append(node("span", "field-label", words(key)));
    const content = node("div", "field-value"); content.append(structured(item, depth + 1)); field.append(content); wrap.append(field);
  }
  return wrap;
}

function details(title, value) {
  const element = node("details", "raw-details");
  element.append(node("summary", "", title), node("pre", "", text(value))); return element;
}

function notice(message, error = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", error);
  $("notice").hidden = !message;
}

async function api(path, payload) {
  const response = await fetch(path, payload === undefined ? { cache: "no-store" } : {
    method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": token }, body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}

function executionFor(id) {
  return state.scenario?.executions?.[id] || state.view.executions?.[state.changed ? "changed" : "initial"]?.[id];
}

function renderCandidates() {
  const candidates = candidatesInOrder();
  if (!candidates.some(candidate => candidate.id === state.selected)) state.selected = candidates[0]?.id;
  $("candidates").replaceChildren();
  if (!candidates.length) $("candidates").append(node("p", "empty", "No validated candidate programs are available yet. The run record preserves its current status."));
  candidates.forEach((candidate, index) => {
    const descendant = Boolean(candidate.parent_ids?.length);
    const card = node("article", "candidate" + (descendant ? " descendant" : "") + (candidate.id === state.selected ? " selected" : ""));
    const top = node("div", "candidate-top");
    top.append(node("span", "candidate-number", descendant ? "DESCENDANT" : "0" + (index + 1)), node("span", "architecture", words(candidate.architecture)));
    card.append(top, node("h3", "", candidate.title), node("p", "", candidate.rationale));
    const tags = node("div", "candidate-tags");
    if (descendant) tags.append(node("span", "badge good", "Parent: " + candidate.parent_ids.join(", ")));
    if (state.view.selection?.selected_id === candidate.id) tags.append(node("span", "badge", "Recruited for investigation"));
    if (descendant && state.view.review?.outcome) tags.append(node("span", "badge " + (state.view.review.outcome === "retain" ? "good" : "bad"), state.view.review.outcome === "retain" ? "Retained for consideration" : "Rejected by fresh reviewer"));
    card.append(tags);
    const execution = executionFor(candidate.id);
    const counts = node("div", "candidate-counts");
    for (const status of ["supported", "conditional", "blocked", "inactive"]) {
      const count = asList(execution?.actions).filter(action => action.status === status).length;
      if (count || status !== "inactive") { const label = node("span"); label.append(node("b", "", execution ? count : "—"), document.createTextNode(status)); counts.append(label); }
    }
    card.append(counts);
    const inspect = node("button", "inspect-button", "Inspect program & dependencies"); inspect.type = "button";
    inspect.setAttribute("aria-pressed", String(candidate.id === state.selected)); inspect.append(node("span", "", "↗"));
    inspect.addEventListener("click", () => { state.selected = candidate.id; renderCandidates(); renderProgram(); }); card.append(inspect);
    $("candidates").append(card);
  });
}

function renderProgram() {
  const candidate = asList(state.view.candidates).find(item => item.id === state.selected);
  $("dependency-trace").replaceChildren();
  if (!candidate) return;
  $("program-title").textContent = candidate.title;
  $("program-id").textContent = candidate.id;
  $("program-json").textContent = JSON.stringify(candidate, null, 2);
  const execution = executionFor(candidate.id);
  if (!execution) { $("dependency-trace").append(node("p", "empty", "Execution is not available for this state yet.")); return; }
  for (const action of asList(execution.actions)) {
    const status = ["supported", "blocked", "conditional", "inactive"].includes(action.status) ? action.status : "conditional";
    const wrap = node("article", "action " + status);
    const heading = node("div", "action-heading"); heading.append(node("h4", "", action.title || action.id), node("span", "status " + status, status));
    wrap.append(heading, node("p", "code-label", action.id));
    const programAction = asList(candidate.actions).find(item => item.id === action.id);
    if (programAction?.description) wrap.append(node("p", "", programAction.description));
    const reasons = asList(action.reasons);
    if (reasons.length) { const list = node("ul"); for (const reason of reasons) list.append(node("li", "", typeof reason === "string" ? reason : text(reason))); wrap.append(list); }
    const facts = {};
    for (const key of ["condition", "prerequisites", "dependencies", "fallbacks"]) if (action[key] !== undefined) facts[key] = action[key];
    const detail = node("details", "raw-details"); detail.append(node("summary", "", "Trace conditions, prerequisites & dependencies"), structured(facts)); wrap.append(detail);
    $("dependency-trace").append(wrap);
  }
}

function renderScenario() {
  $("initial-button").classList.toggle("selected", !state.changed);
  $("changed-button").classList.toggle("selected", state.changed);
  $("initial-button").setAttribute("aria-pressed", String(!state.changed));
  $("changed-button").setAttribute("aria-pressed", String(state.changed));
  $("scenario-banner").classList.toggle("changed", state.changed);
  $("scenario-title").textContent = state.changed ? "Hypothetical contribution unavailable" : "Initial development case";
  const disruption = state.view.disruption;
  const description = disruption?.description || disruption?.summary || disruption?.title;
  $("scenario-copy").textContent = state.changed
    ? (description ? description + " " : "") + "This is a development scenario, not an event attributed to a real institution."
    : "Unknown prerequisites remain unresolved. Supported actions are program outputs, not evidence of political feasibility.";
  $("scenario-label").textContent = state.changed ? "EXPLICITLY HYPOTHETICAL" : "MODEL ASSUMPTIONS";
}

function renderEvidence() {
  const dossier = state.view.dossier || {};
  $("dossier-id").textContent = dossier.id || dossier.version || dossier.dossier_version || "";
  $("sources").replaceChildren();
  for (const source of asList(dossier.sources)) {
    const card = node("article", "source-card");
    card.append(node("span", "code-label", source.id || source.source_id), node("h3", "", source.title), node("p", "", source.publisher || source.organization || "Publisher not recorded"));
    const locator = source.locator || source.section || source.locators;
    if (locator) card.append(node("p", "", "Locator: " + (typeof locator === "string" ? locator : text(locator))));
    const date = source.published_at || source.publication_date || source.date || source.updated_at || "Unknown publication date";
    card.append(node("div", "source-meta", "Published / updated: " + date + " · Retrieved: " + (source.retrieved_at || source.retrieval_timestamp || "Unknown")));
    if (source.url) { const link = safeLink("Open primary source ↗", source.url); link.className = "text-link"; card.append(link); }
    card.append(details("Inspect provenance & permitted excerpt", source)); $("sources").append(card);
  }
  if (!asList(dossier.sources).length) $("sources").append(node("p", "empty", "The dossier has not been loaded."));
  $("claims").replaceChildren();
  for (const claim of asList(dossier.claims)) {
    const item = node("article", "claim"); const top = node("div", "claim-top");
    const type = claim.epistemic_type || claim.type || claim.kind || "unclassified";
    top.append(node("span", "code-label", claim.id || claim.claim_id), node("span", "badge" + (type === "unknown" ? " warning" : ""), words(type)));
    item.append(top, node("p", "", claim.statement || claim.text || claim.claim || claim.description || ""), details("Inspect claim support and locator", claim)); $("claims").append(item);
  }
}

function renderRevision() {
  const view = state.view;
  const container = $("revision-view"); container.replaceChildren();
  const diff = view.semantic_diff;
  if (!diff?.parent_id) { container.append(node("p", "empty", "No worker-produced descendant is available yet. Valid parents and partial run artifacts remain inspectable.")); return; }
  const provenance = node("p", "code-label", diff.parent_id + " → " + diff.child_id);
  container.append(provenance);
  if (view.revision?.change_summary) { const summary = node("p", "revision-summary"); inline(summary, view.revision.change_summary); container.append(summary); }
  const changes = asList(diff.changes);
  const executable = changes.filter(change => change.executable);
  container.append(node("p", "micro", executable.length + " executable field changes · " + (changes.length - executable.length) + " other field changes. Structural differences alone do not establish useful repair."));
  changes.sort((a, b) => Number(Boolean(b.executable)) - Number(Boolean(a.executable))).forEach((change, index) => {
    const row = node("details", "diff-row"); row.open = Boolean(change.executable) && index < 3;
    const heading = node("summary");
    heading.append(node("span", "code-label", change.action_id + " / " + words(change.field)), node("span", "badge" + (change.executable ? " good" : ""), change.executable ? "Executable" : "Narrative / reference"));
    row.append(heading);
    const columns = node("div", "diff-columns");
    for (const [label, value] of [["Before · parent", change.before], ["After · descendant", change.after]]) {
      const column = node("div", "diff-column"); column.append(node("h4", "eyebrow", label));
      column.append(value === null || value === undefined ? node("p", "micro", label.startsWith("Before") ? "Action not present in parent" : "Action removed in descendant") : node("pre", "", text(value))); columns.append(column);
    }
    row.append(columns); container.append(row);
  });
  if (view.revision?.new_weaknesses?.length) {
    const weaknesses = node("div", "revision-weaknesses"); weaknesses.append(node("h3", "", "New weaknesses identified by the revising worker"), structured(view.revision.new_weaknesses)); container.append(weaknesses);
  }
  if (view.revision?.feedback_responses) {
    const responses = node("details", "raw-details"); responses.append(node("summary", "", "Trace worker responses to criticism"), structured(view.revision.feedback_responses)); container.append(responses);
  }
  if (view.retention?.alternatives_preserved) container.append(node("p", "micro", "Preserved alternatives: " + view.retention.alternatives_preserved.join(" · ")));
}

function render() {
  const view = state.view;
  const manifest = view.manifest || {};
  const ui = view.ui || {};
  const status = ui.busy === "live" ? "running" : manifest.status || manifest.outcome || "partial";
  const mode = manifest.mode || manifest.run_mode || manifest.kind || "unknown mode";
  $("run-status").textContent = mode + " · " + status;
  $("run-status").className = "badge " + (["complete", "completed", "passed"].includes(status) ? "good" : ["failed", "blocked"].includes(status) ? "bad" : "warning");
  $("run-id").textContent = manifest.run_id || view.run_dir?.split("/").pop() || "Preserved research run";
  let runDescription = `Status: ${words(status)}. Inspect worker-produced outputs and the preserved execution record below.`;
  if (manifest.mechanism_complete && view.review?.outcome === "reject") runDescription = "The live cycle completed. The fresh reviewer rejected the descendant; this run does not establish successful strategic repair.";
  else if (manifest.mechanism_complete && view.review?.outcome === "retain") runDescription = view.review.substantive_repair
    ? "The live cycle completed. A fresh model reviewer judged the descendant a substantive repair; political feasibility remains unresolved."
    : "The live cycle completed. The descendant was retained for consideration, but useful strategic repair was not established.";
  $("run-description").textContent = ui.busy === "live" ? "A new application-level research cycle is running. Artifacts appear as each checkpoint is saved." : runDescription;
  $("replay-button").disabled = Boolean(ui.busy);
  $("live-button").disabled = Boolean(ui.busy);
  const candidates = asList(view.candidates);
  const parents = candidates.filter(candidate => !candidate.parent_ids?.length).length;
  const descendants = candidates.length - parents;
  const claims = asList(view.dossier?.claims);
  const unknowns = claims.filter(claim => [claim.epistemic_type, claim.type, claim.kind].includes("unknown")).length;
  const calls = manifest.accounting?.cli_invocations ?? manifest.model_calls ?? manifest.actual_model_calls ?? manifest.actual_call_count ?? manifest.call_count ?? (Array.isArray(manifest.calls) ? manifest.calls.length : null);
  const callsLabel = manifest.accounting?.cli_invocations !== undefined ? "Research CLI invocations" : "Recorded model calls";
  $("metrics").replaceChildren();
  for (const [value, label] of [[parents, "Starting approaches"], [descendants, "Preserved descendants"], [unknowns, "Documented unknowns"], [calls ?? "Unknown", callsLabel]]) {
    const metric = node("div", "metric"); metric.append(node("span", "metric-value", value), node("span", "metric-label", label)); $("metrics").append(metric);
  }
  renderScenario(); renderCandidates(); renderProgram(); renderEvidence();
  const selection = view.selection?.selected_id ? {selected_id: view.selection.selected_id, reason: view.selection.reason, rule: view.selection.rule} : null;
  $("selection-view").replaceChildren(structured(selection));
  if (view.selection?.ranking) $("selection-view").append(details("Inspect recruitment ranking & feedback IDs", view.selection));
  const criticism = node("details", "raw-details"); criticism.append(node("summary", "", "Read actual worker criticism · model judgment"), structured(view.criticism)); $("criticism-view").replaceChildren(criticism);
  renderRevision();
  $("review-view").replaceChildren(structured(view.review));
  const review = view.review;
  const verdict = review?.decision || review?.outcome || review?.retention_decision || review?.verdict || (review && Object.keys(review).length ? "Review recorded" : "Awaiting review");
  $("review-badge").textContent = words(verdict);
  $("review-badge").className = "badge " + (/reject|fail/i.test(verdict) ? "bad" : /retain|accept|pass/i.test(verdict) ? "good" : "warning");
  markdown($("brief-content"), typeof view.brief === "string" ? view.brief : view.brief?.markdown);
  $("manifest-json").textContent = JSON.stringify(manifest, null, 2);
  $("record-summary").replaceChildren(structured({ run: manifest.run_id || view.run_dir, mode, status, model_settings: manifest.worker_settings || manifest.model_settings || manifest.worker_configuration || manifest.model || "See manifest for available configuration", accounting: manifest.accounting || {}, usage: manifest.accounting?.usage || manifest.usage || manifest.total_usage || "Unknown", cost: manifest.accounting?.actual_cost ?? manifest.cost ?? manifest.cost_usd ?? "Unknown", interface: "Opening and refreshing this page reads saved artifacts. Replay and scenario execution make no model calls." }));
  $("replay-result").replaceChildren(structured(ui.replay || (view.replay && Object.keys(view.replay).length ? view.replay : "Use Offline replay to validate the preserved run with zero new model calls.")));
  if (ui.live?.error) notice("New live run failed: " + ui.live.error, true);
  else if (ui.view_notice) notice("Run artifacts are still being written. " + ui.view_notice);
}

async function load() {
  if (state.loading) return;
  state.loading = true;
  try { state.view = await api("/api/run"); render(); }
  catch (error) { notice("Unable to load the run: " + error.message, true); }
  finally { state.loading = false; }
}

async function scenario(changed) {
  $("initial-button").disabled = true; $("changed-button").disabled = true;
  try {
    const result = await api("/api/scenario", { changed });
    state.changed = changed; state.scenario = result;
    renderScenario(); renderCandidates(); renderProgram();
    notice(changed ? "Hypothetical case executed against the saved programs. No model calls were made." : "Initial case executed against the saved programs. No model calls were made.");
  } catch (error) { notice("Scenario execution failed: " + error.message, true); }
  finally { $("initial-button").disabled = false; $("changed-button").disabled = false; }
}

for (const tab of document.querySelectorAll(".tab")) tab.addEventListener("click", () => {
  for (const item of document.querySelectorAll(".tab")) { item.classList.toggle("active", item === tab); item.setAttribute("aria-selected", String(item === tab)); }
  for (const panel of document.querySelectorAll(".tab-panel")) panel.hidden = panel.id !== tab.dataset.tab;
});
document.querySelector('a[href="#decision-brief"]').addEventListener("click", () => document.querySelector('[data-tab="workspace"]').click());
$("initial-button").addEventListener("click", () => scenario(false));
$("changed-button").addEventListener("click", () => scenario(true));
$("replay-button").addEventListener("click", async () => {
  $("replay-button").disabled = true; notice("Replaying the saved research outputs…");
  try { const result = await api("/api/replay", {}); notice(`Offline replay: ${result.status || "finished"}. New model calls: ${result.model_calls ?? "see replay record"}.`); await load(); }
  catch (error) { notice("Replay failed: " + error.message, true); }
  finally { $("replay-button").disabled = Boolean(state.view?.ui?.busy); }
});
$("live-button").addEventListener("click", () => {
  $("live-dialog").returnValue = "cancel";
  $("live-dialog").showModal();
});
$("live-dialog").addEventListener("close", async () => {
  if ($("live-dialog").returnValue !== "confirm") return;
  $("live-button").disabled = true;
  try { const result = await api("/api/live", { confirm: "start_new_live_run" }); state.scenario = null; notice("New live run started: " + result.run_id + ". Preserved artifacts will update as workers finish."); await load(); }
  catch (error) { notice("Could not start live run: " + error.message, true); $("live-button").disabled = false; }
});
load();
setInterval(() => {
  if (state.view?.ui?.busy === "live" || state.view?.manifest?.status === "running") load();
}, 4000);

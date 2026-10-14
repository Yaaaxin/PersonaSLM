"""Publish engineering provenance and preserve original document prefixes."""
import argparse
import json
from pathlib import Path
import re
import subprocess

import p1c_design as d
import p1c_scientific_review as r


def append(path,text):
    with Path(path).open('ab') as f:f.write(('\n\n'+text.strip()+'\n').encode('utf-8'))


def document():
    d.require(not (r.OUT/'literature_access_v1.json').exists(),'Refusing duplicate documentation append')
    tests=d.read(r.LOCAL/'full_tests_01.json');d.require(tests['exit_code']==0,'Full tests failed')
    urls=[
        ('https://aclanthology.org/2026.findings-acl.395/','Publication metadata'),
        ('https://aclanthology.org/2026.findings-acl.395.pdf','Primary PDF: methods, FPPS, tradeoffs'),
        ('https://arxiv.org/html/2610.11188v1','Primary full-text sections 3-5: admission, rendering, matched controls'),
        ('https://arxiv.org/html/2410.10813v2','Primary full-text sections 4-5: temporal retrieval, reading'),
        ('https://proceedings.iclr.cc/paper_files/paper/2025/hash/d813d324dbf0598bbdc9c8e79740ed01-Abstract-Conference.html','ICLR publication record'),
        ('https://arxiv.org/html/2610.09772v2','Primary methods/results: clean/polluted paths and structural/raw-text outcomes'),
        ('https://aclanthology.org/2026.findings-acl.103.pdf','Primary methods/results: counterfactual contexts and mutability prompting'),
        ('https://huggingface.co/Qwen/Qwen3.5-2B','Official post-trained model identity and template requirement'),
        ('https://journals.plos.org/plosone/s/criteria-for-publication','Official publication criteria')]
    d.write_json(r.OUT/'literature_access_v1.json',{'registered_utc':d.now(),'mechanism':'Primary URL lookup using web open/find tools; no shell download or code replication.',
        'records':[{'url':u,'inspected_scope':s,'access_status':'ACCESSED','exact_access_timestamp':None} for u,s in urls],
        'limits':'Full-text method sections inspected, not exhaustive appendix/code reproduction; no originality certification.'})
    append('docs/P1c_algorithmic_opportunity_assessment.md',"""
## Scientific-identification review addendum

The unchanged bank and [new counterfactual audit](P1c_counterfactual_pair_audit.md) provide no new model failure observations. They show that R/T switch auxiliary predicates, colors and intervals, with cyclic lexical cues. None supplies a stale target answer. Consequently the present bank cannot validate a remedy for direct outdated-answer competition, even if a future package interaction is observed.

The six five-part assessments above remain in force. The following update links each direction to the newly clarified identification boundary and the [verified prior-art check](P1c_scientific_prior_art_review.md).

| Direction | Observed Failure Modes | Existing Methods and Published Prior Art | Potential Algorithmic Improvements | Validation Feasibility | Publication Value |
|---|---|---|---|---|---|
| Temporal handling | P1b dated errors; P1c date/value coupling, no new outcomes | Time-aware retrieval/interval filtering; LongMemEval | Requested-date handling is a candidate engineering baseline, not an original method | Independent current/historical tasks; full ledger versus reviewed auxiliary selection; ablate date/value cues without deleting trusted evidence | No algorithmic claim until a residual beyond simple rules is identified |
| Relevance gating | H package differences do not establish relevance failure | Admission, random and relevance controls in the admission/presentation study | A future topic/authority distinction must improve on existing gates | Use independent lexical assignments; all-history, no-history, matched random and query-relevance baselines; measure beneficial-memory/fidelity loss | High overlap; present work is identification, not a gate invention |
| Evidence-priority routing | Sufficient evidence coexists with errors, including at C0 | FPPS and source-priority engineering | Explicit provenance routing remains hypothetical | Compare evidence-first and source-label baselines; hidden-state steering requires separately approved infrastructure; test both conflicting and nonconflicting records | Unresolved causal target; no implementation justified |
| Component verification | P1b 137 supported-claim labels versus 110 full answers | Checklists, structured answering and evidence-grounded reading; comprehensive verifier survey incomplete | Detect missing required components without falsely treating them as contradictions | Independent task templates; deterministic checklist, no verifier, published verifier and oracle component labels; separate detection from regeneration | Potential measurement contribution, originality UNVERIFIED |
| Persona/evidence separation | No isolated persona mechanism follows from current R/T bank; S/F held off | AO-DA and FPPS directly overlap | Interaction-aware routing is only a hypothesis | Needs independently replicated S/F/H effects; equal-compute mixed/separated/steered baselines and separate fidelity scoring | Not justified by this auxiliary-history design alone |
| Boundary management | P1b continuation and first-reply success diverge | Native templates, EOS/stops, extraction and structural/raw-text analyses | First establish unit-selection bias; a stop rule is not inherently novel | Independent blinded unit review; frozen parser/native-template/stop and human-span-oracle comparisons; no selection of later answers | Useful validity evidence if reproducible; no new algorithm established |

Implementation complexity and CPU cost remain unmeasured for prospective methods. Deterministic interval/checklist rules are plausible low-cost baselines, while model adjudication, verification/regeneration or two-pass separation add work; no timing claim is made. Fair ablations must separate extra compute, source exclusion, temporal parsing and formatting. Any method must use separate development material and independent evaluation, retain errors/null results, and measure potential persona-fidelity loss independently. No method is approved for implementation or training.
""")
    append('docs/related_work_novelty_matrix.md',"""
## P1c scientific identification review supplement

The [primary-source overlap check](P1c_scientific_prior_art_review.md) revisits personalization steering, memory admission/presentation, temporal retrieval and structural/persona separation. The [counterfactual audit](P1c_counterfactual_pair_audit.md) establishes that the proposed bank concerns auxiliary topical records, not stale target-answer competition. Any prospective contribution must retain that narrower scope and survive independent lexical, date and response-unit checks. No P1c results or original algorithm are claimed; previous matrix entries and historical findings remain intact.
""")
    base=d.read(r.LOCAL/'baseline.json')
    summary=tests['stdout'].strip().splitlines()[-1]
    append('docs/research_development_log.md',f"""
## {d.now()} — P1c scientific identification review and offline audit

Maintainer: Yaxin ZHENG. Objective: audit unchanged P1c relevance/temporal packages, prepare genuine scientific decisions and preserve a reviewable calibration-input snapshot. No inference, new case bank, algorithm implementation, protocol adoption, commit or push was performed.

### Source inspection and preservation

Entry HEAD `{base['git_sha']}`; working tree clean. Entry inventory: {len(base['files'])} tracked files and {len(base['historical_artifacts'])} historical run artifacts. AGENTS, both protocols, requested P1c reports, P1b reports/case-level analyses, original neutral banks/repair records, review forms and tokenizer manifests were read. Baseline creation used the actual project-venv Python inventory command; its recorded UTC, hashes and original document prefixes remain in `results/p1c_scientific_review/v1/baseline.json` and `.before` files. Source prompts, condition IDs and both historical protocols remain unchanged.

### Actual commands and evidence

The exact argv, UTC timestamps, stdout/stderr, exit codes and process durations for substantive build/tokenizer/supplement/test/verification commands are preserved in [engineering logs](validation/p1c/scientific_review_v1/engineering_logs/). Commands executed through `tools/p0_capture.py`: `tools/p1c_scientific_review.py build`, `tools/p1c_scientific_review.py native`, `tools/p1c_scientific_supplement.py`, targeted pytest and full `python -m pytest -q`. Native calls used the existing `llama-tokenize.exe -m <pinned model> --stdin --ids --no-parse-special --offline` vocabulary-only interface, not a completion endpoint. All 72 prompts were retokenized; IDs matched saved records exactly. Native prompt/ID/stdout/stderr logs are retained locally and hash-indexed by the final manifest.

Reference/dependency checks and 72 R/T pair comparisons passed; 480 P1b case contrasts were reconstructed twice with unchanged numerical results. The 135 stored precision scenarios were checked against their inputs and analytical formula; their Monte Carlo simulations were not rerun. Original v1 neutral failures (-1 token for the selected predecessor) and repaired v2 zero differences remain recorded. No stimulus text was changed. H_none is shorter by65 tokens in10 cases and66 in2, a detail that must not be generalized as a constant gap.

### Scientific findings and review package

R changes parcel/music predicate and color; T changes color and interval. All24 T-only pairs preserve predicate but change full propositions; all24 R-only pairs change predicate/value. Twelve off-diagonal pairs share colors because of cyclic construction. All48 active histories omit required answer components and source IDs. Formal auxiliary deletion/substitution leaves all12 references unchanged, but does not exclude model shortcuts. Historical requested dates precede archive recording dates in6 cases; retrospective-state interpretation requires approval. The new12-case,60-text and12-control-subset CSVs retain blank human fields and explicit AI-assisted recommendations. No original human approval was transferred.

New reports cover resolution, counterfactual comparisons, neutral risks, budget/model risks, estimands, review instructions, prior art and the final scientific decision. Existing algorithm assessment and novelty matrix receive append-only updates. Machine artifacts include exhaustive field differences, exact contrast weights, source quotations, native repair links, risk inventory, a proposed addendum and an input snapshot that explicitly does not authorize execution.

### Tests, errors and limitations

Targeted first run:27 passed in0.16s, exit0. Full suite: `{summary}`, exit{tests['exit_code']}; actual process duration {tests['duration_seconds']:.3f}s. No pytest warnings were reported. Native warnings, if present, remain in the per-call logs and are not counted as pytest warnings. Before final integrity execution, review caught JSON integer-key normalization and missing future-manifest link handling in the audit verifier; both checks were corrected without changing data or weakening assertions. No failed generation or fabricated annotation was introduced.

Primary-source literature was accessed via web open/find tools, with inspected scopes and unavailable per-request timestamps recorded in [access ledger](validation/p1c/scientific_review_v1/literature_access_v1.json). No external code replication or exhaustive originality validation is claimed.

### Decision

Technical checks support the unchanged proposal; scientific review and inference authorization remain pending. NO-GO for execution. Minimal next actions are researcher acceptance of narrow package/date interpretation,12-case/60-text reviews including neutral suitability, prospective addendum/outcome approval, and a final authorized logging/resume manifest. Optional budget/Instruct/algorithm extensions are not new mandatory gates. Six clusters, cyclic cues, topic/date/value coupling and unknown future semantic coverage limit inference. The existing72-request order and96-token budget are preserved; P1c outcomes do not exist.
""")
    # Add actual test result without calendar timeline to the consolidated decision report.
    append('docs/P1c_final_scientific_decision.md',f"""
### Completed automated validation

Full project suite: **{summary}**, zero failures, exit {tests['exit_code']}, no reported pytest warnings. The captured process duration was {tests['duration_seconds']:.3f} seconds; this is a test measurement, not an experimental-generation duration. New tests cover reference dependency, R/T package changes, native-ID identity, original-order preservation, blank human fields, repair history, contrast algebra, unknown bounds and nonauthorization. Final hash/link checks are recorded separately; test success is not semantic approval.
""")
    (r.OUT/'engineering_logs').mkdir(exist_ok=True)
    for p in r.LOCAL.glob('*.json'):
        if p.name=='baseline.json':continue
        with (r.OUT/'engineering_logs'/p.name).open('xb') as f:f.write(p.read_bytes())
    return {'documents_appended':3,'full_test_result':summary,'new_generations':0}


def freeze():
    verification=d.read(r.OUT/'verification_v1.json');d.require(verification['status']=='PASS','Integrity incomplete')
    sources=['tools/p1c_scientific_review.py','tools/p1c_scientific_supplement.py','tools/p1c_scientific_finalize.py','tests/test_p1c_scientific_review.py']
    snap=r.OUT/'source_snapshot';snap.mkdir(exist_ok=True)
    for name in sources:
        with (snap/Path(name).name).open('xb') as f:f.write(Path(name).read_bytes())
    for p in r.LOCAL.glob('*.json'):
        if p.name=='baseline.json' or (r.OUT/'engineering_logs'/p.name).exists():continue
        with (r.OUT/'engineering_logs'/p.name).open('xb') as f:f.write(p.read_bytes())
    native={p.as_posix():d.sha(p) for p in (r.LOCAL/'tokenizer_recheck/native_calls').glob('*.json')}
    base=d.read(r.LOCAL/'baseline.json')
    docs=[p for p in Path('docs').glob('P1c_*.md') if p.as_posix() not in base['files']]
    files=list(r.OUT.rglob('*'))+docs+[Path(x) for x in sources+list(r.APPEND_ONLY)]
    files=[p for p in files if p.is_file()]
    prior_sources=[d.DATA,r.V2/'selected_prompts_v2.json',r.V2/'configuration_proposal_v2.json',d.PUBLIC/'condition_definitions_v1.json',d.PUBLIC/'applicability_v1.csv',d.PUBLIC/'precision_simulation_v1.json','docs/research_protocol_v1.1.md','docs/PersonaSLM_Research_Protocol_v1.2_Revised_Proposed_r1.md']
    result={'version':'p1c_scientific_review_reproducibility_v1','created_utc':d.now(),
        'status':'OFFLINE_REVIEW_COMPLETE_SCIENTIFIC_APPROVAL_PENDING','git_sha':base['git_sha'],
        'entry_git_dirty':base['git_status'],'final_git_status':subprocess.check_output(['git','status','--short'],text=True),
        'source_hashes':{str(p).replace('\\','/'):d.sha(p) for p in prior_sources},
        'files':{p.as_posix():d.sha(p) for p in files},'native_recheck_logs':native,
        'baseline_inventory_sha256':d.sha(r.LOCAL/'baseline.json'),
        'historical_scope':verification,'native_identity':d.read(r.OUT/'native_reverification_v1.json')['identity'],
        'new_generations':0,'human_approval':'OPEN','inference_authorized':False,
        'immutability':'Exclusive creation; source snapshots and hashes reject silent replacement. Not filesystem write protection or researcher approval.',
        'timing_scope':'Engineering timestamps are actual captures; no review date is invented.',
        'final_manifest_self_hash':'Not included to avoid circular hashing; external reviewer may hash this file.'}
    d.write_json(r.OUT/'reproducibility_manifest_v1.json',result)
    return {'hashed_files':len(files),'native_recheck_logs':len(native),'new_generations':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['document','freeze']);a=p.parse_args()
    print(json.dumps(document() if a.action=='document' else freeze()))

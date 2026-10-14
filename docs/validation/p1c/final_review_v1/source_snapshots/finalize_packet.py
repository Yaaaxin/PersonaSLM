"""Record actual offline preparation evidence; never execute generation."""
from pathlib import Path
import json
import re
import subprocess
import sys

sys.path.insert(0, str(Path.cwd()/'tools'))
import p1c_design as d
import p1c_final_review as f
import p1c_scientific_review as a

base=d.read(f.LOCAL/'baseline.json')
tests=d.read(f.LOCAL/'full_tests_01.json')
d.require(tests['exit_code']==0 and '796 passed' in tests['stdout'],'Unexpected test result')
oldnative=d.read(a.V2/'reproducibility_manifest_v1.json')['native_call_logs']
for p,h in oldnative.items():d.require(d.sha(p)==h,'Original native log changed: '+p)
recomputed=d.history_evidence()
d.require(recomputed==d.read(a.OUT/'p1b_evidence_recheck_v2.json'),'P1b case-level evidence differs')

# Preserve exact old report versions before appending current technical history.
for name in f.APPEND:
    src=f.LOCAL/(Path(name).name+'.before')
    dest=f.OUT/'source_snapshots'/(Path(name).name+'.before')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream:stream.write(src.read_bytes())
with Path('docs/research_development_log.md').open('ab') as stream:
    stream.write(('\n\n## P1c final researcher-review and calibration candidate preparation\n\n'
        +'Engineering record created: '+d.now()+'. Maintainer: Yaxin ZHENG.\n\n'
        +'Entry HEAD: `'+base['git_sha']+'`; working tree clean at entry. All changes remain uncommitted. '
        +'No generation, model training, algorithm implementation, protocol modification or new experimental cell.\n\n'
        +'Objective: convert the existing identification audit into concrete case/text proposals and a complete disabled 72-request candidate. '
        +'Implemented `tools/p1c_final_review.py` and 15 acceptance guards; original stimuli and order retained. '
        +'Twelve case proposals are ACCEPT_WITH_RESTRICTED_ESTIMAND. Sixty text operational labels are 32 PASS and 28 UNCERTAIN; '
        +'the 12 neutral assessments are a subset, not additional items. Strict neutrality/isolated-mechanism criteria remain FAIL where applicable. '
        +'No human judgment, identity or review timestamp was supplied or inferred.\n\n'
        +'Reports: P1c_final_researcher_review_packet, P1c_final_identification_decision, P1c_final_estimand_registry, '
        +'P1c_calibration_freeze_readiness, P1c_protocol_addendum_proposal; append-only algorithmic assessment update. '
        +'Machine records are in `docs/validation/p1c/final_review_v1/`; original inputs and prior report snapshots are pinned in the new provenance manifest.\n\n'
        +'Actual commands, with stdout/stderr, timestamps and return codes, are preserved in the new engineering_logs: '
        +'`.venv\\Scripts\\python.exe tools/p1c_final_review.py build`; '
        +'`.venv\\Scripts\\python.exe -m pytest -q tests/test_p1c_final_review.py` (15 passed in 0.91s); '
        +'`.venv\\Scripts\\python.exe tools/p1c_final_review.py verify`; '
        +'`.venv\\Scripts\\python.exe -m pytest -q` (796 passed in 32.01s); '
        +'`.venv\\Scripts\\python.exe results/p1c_final_review/v1/finalize_packet.py`; '
        +'`git rev-parse HEAD`; `git status --short`; final compile/diff checks have separate captures. '
        +'The p0_capture wrapper records each executed child argv; no review time is inferred from engineering time.\n\n'
        +'Verification: all 72 saved native token-ID arrays and prompt bytes rechecked; current pinned model/backend/tokenizer/DLL hashes rechecked; '
        +'12 zero-difference active/neutral sets. No fresh tokenizer or generation calls were needed. '
        +'Historical scope: 5,798 run artifacts, 1,234 original tokenizer logs and 72 later recheck logs; prior chain audits retained, not re-executed. '
        +'P1b 480 case-level contrast values reconstructed against their preserved analysis. All 597 entry files remain unchanged except append-only prefixes of the two named log/report files.\n\n'
        +'Read-only search correction: a Windows rg path wildcard `src/personaslm/p1b*` produced an OS path error; '
        +'the directory search with `-g` filtering was used instead. That console diagnostic was not a generation or a failed validation test; '
        +'its full original command capture is unavailable, so none is fabricated. No model-output or reference repair was necessary.\n\n'
        +'Scientific decision: recommend scoped development acceptance, but scientific review, limited neutral suitability, addendum/evaluation approval and '
        +'explicit 72-request inference authorization remain pending. Six clusters cannot establish population interaction precision. '
        +'No claim of pure temporal mechanism, stale-answer competition, algorithmic novelty or publication readiness. '
        +'Primary prior-art methods were reused from the earlier verified audit; CoVe and RARR method sections were additionally inspected. '
        +'Independent data and annotation remain future publication needs, not invented additional gates for this development packet.\n').encode('utf-8'))

verification=f.verify()
verification.update(original_tokenizer_logs_preserved=len(oldnative),p1b_case_contrasts_reconstructed=480,
                    automated_tests={'passed':796,'exit_code':tests['exit_code'],'capture':'engineering_logs/full_tests_01.json'})
d.write_json(f.OUT/'verification_v1.json',verification)
for p in f.LOCAL.glob('*_01.json'):
    dest=f.OUT/'engineering_logs'/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as stream:stream.write(p.read_bytes())
for p in [Path('tools/p1c_final_review.py'),Path('tests/test_p1c_final_review.py'),Path(__file__)]:
    dest=f.OUT/'source_snapshots'/p.name
    with dest.open('xb') as stream:stream.write(p.read_bytes())
newdocs=[Path('docs')/n for n in ['P1c_final_researcher_review_packet.md','P1c_final_identification_decision.md',
    'P1c_final_estimand_registry.md','P1c_calibration_freeze_readiness.md','P1c_protocol_addendum_proposal.md']]
broken=[]
for p in newdocs+[Path('docs/P1c_algorithmic_opportunity_assessment.md')]:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if link.startswith(('http:','https:','#')):continue
        target=(p.parent/link.split('#')[0]).resolve()
        if target== (f.OUT/'reproducibility_manifest_v1.json').resolve():continue
        if not target.exists():broken.append([str(p),link])
d.require(not broken,'Broken report links: '+str(broken))
files=list(f.OUT.rglob('*'))+newdocs+[Path(p) for p in f.APPEND]+[Path('tools/p1c_final_review.py'),Path('tests/test_p1c_final_review.py')]
manifest={'version':'p1c_final_review_reproducibility_v1','created_utc':d.now(),
    'maintainer':'Yaxin ZHENG','annotation_provenance':'AI-assisted proposals only; no human approval registered',
    'git_sha':base['git_sha'],'entry_git_dirty':bool(base['git_status']),
    'git_status_at_freeze':subprocess.check_output(['git','status','--short','--untracked-files=all'],text=True),
    'files':{p.as_posix():d.sha(p) for p in files if p.is_file()},
    'original_entry_inventory':base['files'],'historical_artifact_inventory':base['historical_artifacts'],
    'original_tokenizer_logs':oldnative,'native_recheck_logs':d.read(a.OUT/'reproducibility_manifest_v1.json')['native_recheck_logs'],
    'append_only_rule':'Original algorithm report and development log prefixes preserved byte-for-byte in source_snapshots/*.before; old manifest hashes refer to those versions.',
    'native_scope':'Existing actual native calls validated against unchanged prompts and binaries; no new tokenizer process or generation.',
    'literature_scope':{'earlier_verified_sources':'docs/P1c_scientific_prior_art_review.md',
        'new_primary_methods_inspected':['https://aclanthology.org/2024.findings-acl.212.pdf','https://aclanthology.org/2023.acl-long.910.pdf'],
        'scope':'Method sections and publication records; no algorithm implementation or exhaustive novelty proof. Exact access times not recorded.'},
    'documentation_links':'PASS','tests_capture':'engineering_logs/full_tests_01.json',
    'new_generations':0,'scientific_approval':'PENDING','execution_authorized':False,
    'self_hash':'External receipt; this file excludes itself to avoid circular hashing.'}
d.write_json(f.OUT/'reproducibility_manifest_v1.json',manifest)
d.write_json(f.OUT/'reproducibility_manifest_sha256_v1.json',{'path':(f.OUT/'reproducibility_manifest_v1.json').as_posix(),
    'sha256':d.sha(f.OUT/'reproducibility_manifest_v1.json')})
print(json.dumps({'files_pinned':len(manifest['files']),'historical_artifacts':len(base['historical_artifacts']),
    'original_native_logs':len(oldnative),'documentation_links':'PASS','tests':796,'new_generations':0},indent=2))

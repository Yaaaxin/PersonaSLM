"""Preserve actual offline importer-preparation records; no scientific registration."""
import csv
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path.cwd()/'tools'))
import p1c_design as d
import p1c_decisions as p

local=Path('results/p1c_decision_gate/v1');base=d.read(local/'baseline.json')
tests=d.read(local/'tests_02.json');gate=d.read(p.PACKAGE/'current_gate_status_v1.json')
d.require(tests['exit_code']==0 and '105 passed' in tests['stdout'],'Unexpected tests')
d.require(gate['status']=='NO_GO' and gate['valid_registered_unique_decisions']==0,'Unexpected actual review state')
with Path('docs/research_development_log.md').open('ab') as stream:
    stream.write(('\n\n## P1c researcher-decision importer and final offline execution gate\n\n'
        +'Engineering record: '+d.now()+'. Maintainer: Yaxin ZHENG.\n\n'
        +'Entry HEAD `'+base['git_sha']+'`; entry tree clean. Narrow workflow only: no new stimulus, model inference, '
        +'algorithm implementation, protocol adoption, or broad repeated audit. Original 77-row confirmation form and all review sources remain untouched. '
        +'All actual human fields were empty; no completed researcher decisions were located or registered.\n\n'
        +'Implemented `tools/p1c_decisions.py` with prepare, validate, register and offline gate actions. '
        +'Created a separate 72-row decision template, scientific approval template, explicit authorization template, source pins and analysis overlay. '
        +'The 12 matched texts keep original N_history IDs and receive LENGTH_MATCHED_DIAGNOSTIC_CONTROL only in analysis metadata. '
        +'This is an interpretation restriction, not semantic approval. Twelve linked control assessments are not extra independent items. '
        +'Importer preserves raw input bytes, corrections and unavailable review timestamps, rejects inconsistent sources/labels/IDs/duplicate JSON keys, '
        +'and cannot infer inference authorization from completed scientific forms. Negative decisions may be registered but block GO.\n\n'
        +'Actual commands are captured under `docs/validation/p1c/decision_gate_v1/engineering_logs/`: '
        +'`.venv\\Scripts\\python.exe tools/p1c_decisions.py prepare`; '
        +'`.venv\\Scripts\\python.exe -m pytest -q tests/test_p1c_decisions.py tests/test_p1c_final_review.py tests/test_p1c_scientific_review.py`; '
        +'`.venv\\Scripts\\python.exe tools/p1c_decisions.py gate --output docs/validation/p1c/decision_gate_v1/current_gate_status_v1.json`; '
        +'`.venv\\Scripts\\python.exe -m py_compile tools/p1c_decisions.py tests/test_p1c_decisions.py`; '
        +'`.venv\\Scripts\\python.exe results/p1c_decision_gate/v1/finalize.py`. '
        +'Git HEAD/status and final diff checks were read-only. No commit or push.\n\n'
        +'First focused suite: 102 passed in 2.37s. After adding duplicate-JSON and malformed-policy guards: '
        +'105 passed in 2.42s (60 new cases plus 45 existing review guards), zero pytest failures/warnings. '
        +'The full unrelated suite was not rerun; its prior 796 result remains historical. Synthetic test decisions exist only in temporary unit-test fixtures, '
        +'not scientific registration directories.\n\n'
        +'The actual gate returned NO_GO with expected child exit code 2 (capture wrapper nonzero), not a technical/test failure. '
        +'Technical checks passed for 45 pinned sources, 72 preserved prompts/real token-ID records, model/backend/tokenizer/DLL identity, references and routing. '
        +'Outstanding: 72 unique item decisions, 12 linked diagnostic assessments, five policy approvals and separate exact-72 authorization. '
        +'Original manifest SHA-256 remains '+p.MANIFEST_SHA+'. No new manifest, randomization or output-budget change.\n\n'
        +'Existing algorithm assessments and verified prior-art references were retained, not rewritten or presented as new discoveries. '
        +'Package estimands, six-speaker precision limits, structural censoring and the need for later independent validation remain. '
        +'No substantive implementation errors occurred; missing approval is the intentional scientific gate outcome.\n').encode('utf-8'))

for name,h in base['files'].items():
    if name=='docs/research_development_log.md':
        before=local/'research_development_log.md.before'
        d.require(d.sha(before)==h and Path(name).read_bytes().startswith(before.read_bytes()),'Log prefix changed')
    else:d.require(d.sha(name)==h,'Original tracked file changed: '+name)
for name,h in d.read(p.PACKAGE/'source_pins_v1.json')['files'].items():
    d.require(d.sha(name)==h,'Frozen source changed: '+name)
for file in p.PACKAGE.glob('*.json'):d.read(file)
headers,rows=p.csv_rows(p.PACKAGE/'researcher_item_decisions_v2.csv')
d.require(all(r[k]=='' for r in rows for k in p.HUMAN_FIELDS),'Human fields were populated')
doc=Path('docs/P1c_decision_registration_and_execution_gate.md');pending=p.PACKAGE/'reproducibility_manifest_v1.json'
for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
    if link.startswith(('http:','https:','#')):continue
    target=(doc.parent/link.split('#')[0]).resolve()
    d.require(target.exists() or target==pending.resolve(),'Broken link: '+link)
for file in local.glob('*_01.json'):
    if file.name=='baseline.json':continue
    target=p.PACKAGE/'engineering_logs'/file.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(file.read_bytes())
file=local/'tests_02.json';target=p.PACKAGE/'engineering_logs'/file.name
with target.open('xb') as stream:stream.write(file.read_bytes())
for file in [Path('tools/p1c_decisions.py'),Path('tests/test_p1c_decisions.py'),Path(__file__),local/'research_development_log.md.before']:
    target=p.PACKAGE/'source_snapshots'/file.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(file.read_bytes())
files=[x for x in p.PACKAGE.rglob('*') if x.is_file()]+[doc,Path('tools/p1c_decisions.py'),Path('tests/test_p1c_decisions.py'),Path('docs/research_development_log.md')]
manifest={'version':'p1c_decision_gate_reproducibility_v1','created_utc':d.now(),'git_sha':base['git_sha'],
    'entry_git_dirty':False,'git_status_at_freeze':subprocess.check_output(['git','status','--short','--untracked-files=all'],text=True),
    'original_entry_file_hashes':base['files'],'entry_files_preserved':len(base['files']),
    'allowed_append_only_file':'docs/research_development_log.md; exact previous bytes preserved in source_snapshots',
    'files':{x.as_posix():d.sha(x) for x in files},'manifest_sha256_unchanged':p.MANIFEST_SHA,
    'tests':{'selected_suite':105,'new_cases':60,'exit_code':0,'full_suite_rerun':False},
    'human_registered_decisions':0,'human_review_timestamps_created':False,'new_generations':0,
    'historical_scope':'All 638 entry tracked files preserved except an append-only development-log extension; raw experiment directories were not written. Earlier broad raw-output audits retained, not rerun.',
    'gate_status':'NO_GO','validation':'PASS','documentation_links':'PASS'}
d.write_json(pending,manifest)
d.write_json(p.PACKAGE/'reproducibility_receipt_v1.json',{'manifest_sha256':d.sha(pending)})
print({'entry_files_preserved':len(base['files']),'records_registered':0,'tests_passed':105,'gate':'NO_GO','new_generations':0})

"""P1-only prospective O/Q recovery. No inference in this module.

Historical files are read-only. A non-unique Q1 component blocks its requests;
the original component order is not silently invented as a tie-breaking rule.
"""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path
import re
import unicodedata

import p1_measurement_run as old
import p1_measurement_scoring_v2 as scorer

s, m = old.s, old.m
OUT = Path('docs/validation/p1/measurement_recovery_2x2_v1')
ROOT = Path('results/p1_measurement_recovery/v1')
OLD = old.OUT
FAMILIES = ('single_lookup', 'dual_component', 'relational_chain', 'dated_comparison')


def cases():
    return s.load(OLD/'materials_v1.json')['cases']


def select_cases(bank):
    # Only identity, pool and task family are consulted. Never any model score.
    return [c for family in FAMILIES for c in sorted(
        (c for c in bank if c['pool']=='calibration' and c['family']==family),
        key=lambda c:c['case_id'])[:2]]


def evidence_line(f):
    return f"[{f['source_id']}] {f['entity']} | {f['attribute']} = {f['value']} | valid {f['valid_from']} through {f['valid_to']}."


def organized_evidence(c):
    """Reorder original evidence lines, adding only entity group headings."""
    lines=[]; previous=None
    for f in sorted(c['facts'],key=lambda x:(x['entity'],x['valid_from'],x['valid_to'],x['attribute'],x['source_id'])):
        if f['entity']!=previous:
            if lines: lines.append('')
            lines.append('Entity: '+f['entity']);previous=f['entity']
        lines.append(evidence_line(f))
    return '\n'.join(lines)


def reference_audit(c):
    by_id={f['source_id']:f for f in c['facts']}; witnesses=[]
    s.require(Counter(c['trusted_evidence'].splitlines())==Counter(evidence_line(f) for f in c['facts']), 'Evidence rendering mismatch')
    for f in c['facts']:
        s.require(f['valid_from']<=f['valid_to'],'Inverted validity interval')
    for r in c['reference']:
        date='2051-03-15' if r['key']=='march_bay' else '2051-09-15' if r['key']=='september_bay' else c['requested_date']
        chain=[by_id[x] for x in r['source_ids']]
        s.require(chain[0]['entity']==c['speaker_name'],'Reference starts at wrong entity')
        for i,f in enumerate(chain):
            s.require(f['valid_from']<=date<=f['valid_to'],'Reference outside requested interval')
            candidates=[x for x in c['facts'] if x['entity']==f['entity'] and x['attribute']==f['attribute'] and x['valid_from']<=date<=x['valid_to']]
            s.require(len(candidates)==1 and candidates[0]==f,'Non-unique reference witness')
            if i:s.require(chain[i-1]['value']==f['entity'],'Broken reference chain')
        s.require(chain[-1]['value']==r['value'],'Reference value mismatch')
        witnesses.append({'component':r['key'],'requested_date':date,'witnesses':chain})
    return {'status':'PASS_OBJECTIVE_WITNESS_CHECKS_NOT_HUMAN_VALIDATION','components':witnesses}


def q1_candidates(c):
    by_id={f['source_id']:f for f in c['facts']}
    eligible=[]
    for r in c['reference']:
        # An administrative bay/zone/gate identifier denotes an entity. Time
        # windows are not an entity or a single date under the authorized rule.
        if not re.fullmatch(r'(?:Bay [BD]\d+|Zone Z\d+|Gate G\d+|\d{4}-\d{2}-\d{2})',r['value']):continue
        chain=[by_id[x] for x in r['source_ids']]
        if all(f['valid_from']<=c['requested_date']<=f['valid_to'] for f in chain):eligible.append(r)
    if eligible:return eligible
    first=c['reference'][0]
    if re.fullmatch(r'(?:Bay [BD]\d+|Zone Z\d+|Gate G\d+|\d{4}-\d{2}-\d{2})',first['value']):return [first]
    return []


def q1(c, *, ordered_tie_authorized=False):
    eligible=q1_candidates(c)
    s.require(bool(eligible),'Q1_INELIGIBLE_NO_ENTITY_OR_DATE')
    s.require(len(eligible)==1 or ordered_tie_authorized,'Q1_COMPONENT_PRIORITY_UNRESOLVED: '+c['case_id'])
    ref=eligible[0]
    # No answer string is added to the question. All selected answers are bays.
    s.require(ref['value'].startswith('Bay '),'Q1 question template does not cover this component')
    question=f"Which bay is assigned to {c['speaker_name']} on {c['requested_date']}? Give exactly one bay identifier."
    return {'question':question,'reference':[copy.deepcopy(ref)],'aliases':[ref['value'],ref['value'].split(' ',1)[1]],
        'candidate_components':[r['key'] for r in eligible], 'selected_component':ref['key'],
        'selection':'Unique eligible entity/date component' if len(eligible)==1 else 'Researcher-clarified original-order tie break',
        'requested_date':c['requested_date']}


def normalize_single(text):
    # Frozen before new generation. No substring extraction, prose deletion,
    # negation removal, value replacement or post-output alias expansion.
    value=' '.join(unicodedata.normalize('NFKC',text).split()).casefold()
    if value.endswith('.'):value=value[:-1].rstrip()
    return value


def score_single(text, specification, applicable=True, identifiable=True):
    if not applicable:return {'task_success':'N/A','answer_state':'Not Applicable'}
    if text is None:return {'task_success':'Missing','answer_state':'Missing'}
    if not identifiable:return {'task_success':'Uncertain','answer_state':'Unverifiable','reason':'BOUNDARY_UNRESOLVED'}
    value=normalize_single(text)
    if value in {normalize_single(a) for a in specification['aliases']}:
        return {'task_success':'Success','answer_state':'Correct','reason':'Exact whole-answer frozen alias'}
    if not value:return {'task_success':'Failure','answer_state':'Missing','reason':'Observed empty response, distinct from absent record'}
    if re.fullmatch(r'(?:bay )?[bd]\d+',value):
        return {'task_success':'Failure','answer_state':'Incorrect','reason':'Unambiguous wrong bay identifier'}
    return {'task_success':'Uncertain','answer_state':'Unverifiable','reason':'Outside frozen single-answer grammar; semantic audit required'}


def adjudicated_decision(rows):
    """Only real registered human labels may enter the developmental gate."""
    groups={d:[r for r in rows if r['condition']==d] for d in ('D0','D1','D2','D3')}
    if any(len(g)!=8 for g in groups.values()) or any(not r.get('researcher_decision') for r in rows):
        return {'status':'SCIENTIFIC DECISION PENDING REVIEW','selected_configuration':None}
    s.require(len(rows)==32 and len({(r['condition'],r['case_id']) for r in rows})==32,'Gate inventory')
    s.require(all(r['researcher_decision'] in ('Success','Failure','Uncertain','Missing','N/A') for r in rows),'Invalid human task label')
    for d,g in groups.items():
        if sum(r['researcher_decision']=='Success' for r in g)>=6 and sum(r['researcher_decision']==r['automatic_task_success'] for r in g)>=7:
            failed_families=[f for f in FAMILIES if not any(r['family']==f and r['researcher_decision']=='Success' for r in g)]
            return {'status':'QUALIFIED_FOR_PROSPECTIVE_PREPARATION_ONLY','selected_configuration':d,'families_not_measurement_ready':failed_families,'new_inference_authorized':False}
    return {'status':'NO_CONFIGURATION_QUALIFIED','selected_configuration':None,'new_prompt_variants_permitted':False}


# Item-level audit after reading all original outputs and evidence. These are
# AI review recommendations, not a second independent annotator or human truth.
FAILURES={
 0:['OUTDATED_VALUE_SELECTED'],1:['NOT_YET_VALID_VALUE_SELECTED'],2:['FALSE_UNAVAILABILITY','INCOMPLETE_REASONING_TAIL'],
 3:['NOT_YET_VALID_VALUE_SELECTED'],4:[],5:['NOT_YET_VALID_VALUE_SELECTED'],
 6:['WRONG_DATE_ATTACHMENT','SELF_CONTRADICTION','INCOMPLETE_ANSWER_COMPONENTS'],
 7:['WRONG_DATE_ATTACHMENT','SELF_CONTRADICTION','INCOMPLETE_ANSWER_COMPONENTS'],
 8:['OUTDATED_VALUE_SELECTED'],9:[],10:['WRONG_ENTITY','TEMPORAL_INTERPRETATION_UNCERTAIN','INCOMPLETE_REASONING_TAIL'],
 11:['INCOMPLETE_CITATION_WITH_COMPLETE_ANSWER'],12:[],13:[],
 14:['WRONG_DATE_ATTACHMENT','EXPLICIT_INTERVAL_REASONING_ERROR','INCOMPLETE_ANSWER_COMPONENTS'],
 15:['REVERSED_DATE_ATTACHMENTS','INCOMPLETE_REASONING_TAIL'],16:['OUTDATED_VALUE_SELECTED'],17:[],
 18:['OUTDATED_VALUE_SELECTED'],19:[],20:['OUTDATED_VALUE_SELECTED'],21:[],
 22:['FALSE_UNAVAILABILITY','INCOMPLETE_REASONING_TAIL'],23:['REVERSED_DATE_ATTACHMENTS','INCOMPLETE_REASONING_TAIL'],
 24:[],25:[],26:['OUTDATED_VALUE_SELECTED'],27:['OUTDATED_COMPONENT_SELECTED'],28:[],29:['OUTDATED_VALUE_SELECTED'],
 30:['WRONG_ENTITY','TEMPORAL_INTERPRETATION_UNCERTAIN','INCOMPLETE_REASONING_TAIL'],31:['REVERSED_DATE_ATTACHMENTS','INCOMPLETE_REASONING_TAIL']}


def original_audit():
    bank={c['case_id']:c for c in cases()};path=OLD/'A_C0/measurement_v1'
    ai=s.load(path/'joined_AI_proposals_v1.json');auto={x['review_id']:x for x in s.load(path/'automatic_v2_review_text_v1.json')}
    archived=old.audit('A_C0');requests={x['request']['case_id']:x for x in archived['rows']}
    template=Path(s.load(OLD/'A_C0_manifest_v1.json')['template_path']).read_text(encoding='utf-8')
    selected={c['case_id'] for c in select_cases(list(bank.values()))}; rows=[]
    for x in sorted(ai,key=lambda x:x['case_id']):
        c=bank[x['case_id']];a=auto[x['review_id']];entry=requests[c['case_id']];req=entry['request'];res=entry['result']
        reconstructed=s.render(template,[{'role':'user','content':m.content(c,'C0')}])
        s.require(reconstructed.encode()==req['prompt'].encode(),'D0 prompt byte mismatch')
        s.require(res['raw_response']==x['evaluation_text'] and s.th(res['raw_response'])==x['raw_sha256'],'Original evaluation view changed')
        s.require(scorer.score(x['evaluation_text'],c,True)=={k:v for k,v in a.items() if k!='review_id'},'Frozen automatic scorer reconstruction differs')
        witness=reference_audit(c); flags=list(FAILURES[int(c['case_id'][-2:])])
        disagreements=[k for k in ('task_success','factual','temporal','semantic_completeness') if a[k]!=x[k]]
        if disagreements:flags.append('EVALUATOR_DISAGREEMENT_NOT_PROOF_OF_SCORER_ERROR')
        if c['family']=='dated_comparison':flags.append('AUTOMATIC_DATE_ATTACHMENT_COVERAGE_LIMIT')
        rationale=x['claim_and_task_reason']
        if c['case_id'].endswith('14'):rationale+=' The explicit claim that March falls inside July-December is independently false calendar reasoning.'
        if c['case_id'].endswith(('02','22')):rationale+=' Negative answer delivery versus missing requested value remains a completeness-policy disagreement; both imply task failure.'
        if c['case_id'].endswith('30'):rationale+=' An Incorrect temporal alternative is defensible because D6507 also expires before September; do not equate error attribution with observable temporal validity.'
        if c['case_id'].endswith('10'):rationale+=' The cited interval itself contains the query date; entity error alone does not settle the temporal construct.'
        rows.append({'case':c,'original_request':req,'original_result':res,'original_AI':x,'automatic_v2':a,
            'reference_audit':witness,'D0_prompt_byte_identical':True,'D0_reused_in_2x2':c['case_id'] in selected,
            'original_run_directory':archived['run_directory'],'proposed_failure_type':flags,
            'evidence_rationale':rationale,'disagreement_metrics':disagreements,
            'audit_recommendation':'Retain original task-success proposal pending researcher review; no source score overwritten',
            'researcher_decision':'','researcher_notes':'','provenance':'AI_ASSISTED_SOURCE_AUDIT_NOT_INDEPENDENT_OR_HUMAN_VALIDATED'})
    return rows


def prepare_audit():
    s.require(not (OUT/'original_C0_audit_v1.json').exists(),'Preserve existing audit')
    s.require(old.cumulative()['attempted']=={'A_C0':32,'B_FACTORIAL':0,'C_DIAGNOSTIC':16},'Reconcile prior requests before new allocation')
    sealpath=OLD/'reproducibility_manifest_v1.json'; seal=s.load(sealpath)
    mismatches=[p for p,h in seal['artifact_sha256'].items() if s.sha256(Path(p))!=h]
    s.require(not mismatches,'Previous sealed artifacts changed: '+str(mismatches))
    s.save(OUT/'preservation_baseline_v1.json',{'source_seal':sealpath.as_posix(),'source_seal_sha256':s.sha256(sealpath),
        'verified_count':len(seal['artifact_sha256']),'registered_utc':s.b.utc_now(),
        'log_sha256':s.sha256(Path('docs/research_development_log.md'))})
    log=OUT/'research_development_log_before_v1.bin';log.write_bytes(Path('docs/research_development_log.md').read_bytes())
    selected=select_cases(cases()); s.require(len(selected)==8 and Counter(c['family'] for c in selected)==Counter({f:2 for f in FAMILIES}),'Selection inventory')
    s.save(OUT/'case_inventory_frozen_v1.json',{'phase':'P1','registered_utc':s.b.utc_now(),
        'selection_rule':'For each fixed task family, take the first two calibration case IDs in ascending lexical order; never consult outcomes.',
        'case_ids':[c['case_id'] for c in selected], 'cases':selected,'outcome_blind_algorithm':True,
        'limitation':'Previously observed development bank; deterministic selector is outcome-independent, not a blinded new sample. Eight-row burden and Alderbrook ancestry overrepresented.',
        'Q1_candidates':{c['case_id']:q1_candidates(c) for c in selected},
        'Q1_ambiguity':{c['case_id']:[r['key'] for r in q1_candidates(c)] for c in selected if len(q1_candidates(c))!=1}})
    audit=original_audit();s.save(OUT/'original_C0_audit_v1.json',audit)
    return {'status':'OFFLINE_AUDIT_PREPARED','rows':len(audit),'D0_reused':sum(r['D0_reused_in_2x2'] for r in audit),
        'Q1_priority_unresolved':[c['case_id'] for c in selected if len(q1_candidates(c))!=1], 'new_generations':0}


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(prepare_audit(),indent=2))

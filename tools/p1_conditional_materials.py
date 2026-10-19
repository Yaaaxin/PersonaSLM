"""Freeze mutually exclusive P1 pilot candidates; tokenize only, never infer."""
import argparse
import ast
from collections import Counter
import copy
import json
from pathlib import Path
import random
import p1_recovery_v2 as r
import p1_temporal_fallback as fallback
import p1_blinded_audit as blind
from personaslm_alignment import contrasts

s,d,m=r.s,r.d,r.m
OUT=blind.OUT
MANIFESTS=OUT/'manifests'
CONFIGS=('D0','D1','D2','D3')
SOURCE_KEYS=('model','template_path','template_sha256','candidate_metadata_sha256','decoding_policy','native_tokenizer_identity')
ORDER_SEEDS={'C0':731960,'remaining':731961}


def request_hash(row):
    return s.th(json.dumps({k:v for k,v in row.items() if k!='request_sha256'},sort_keys=True,separators=(',',':')))


def ordered(rows):
    head=sorted([q for q in rows if q['condition']=='C0'],key=lambda q:q['case_id'])
    tail=sorted([q for q in rows if q['condition']!='C0'],key=lambda q:(q['case_id'],q['condition']))
    random.Random(ORDER_SEEDS['C0']).shuffle(head);random.Random(ORDER_SEEDS['remaining']).shuffle(tail)
    return head+tail


def source_token_cache():
    cache={}
    for path in (d.OLD/'B_FACTORIAL_manifest_v1.json',fallback.OUT/'fallback_pilot_manifest_candidate_v1.json',fallback.OUT/'fallback_calibration_manifest_candidate_v1.json'):
        plan=s.load(path)
        for req,log in zip(plan['requests'],plan['native_tokenizer_logs']):
            s.require(s.sha256(Path(log['path']))==log['sha256'],'Source token log changed')
            native=s.load(log['path']);ids=ast.literal_eval(native['stdout'].strip())
            s.require(native['returncode']==0 and ids==req['input_token_ids'] and native['prompt']==req['prompt'],'Source native mismatch')
            cache[req['prompt_sha256']]={'prompt':req['prompt'],'ids':ids,'log':log,'source_manifest':path.as_posix()}
    return cache


def factual_audit(c):
    witness=d.reference_audit(c)
    current=c['reference'][0]['value'] if 'stale_endpoint' not in c else c['stale_endpoint']['current_value']
    old=c['old_reference']['value'] if 'old_reference' in c else c['stale_endpoint']['old_value']
    assert current!=old
    # Preserve old value only in dated H, apart from its valid trusted ledger record.
    for name in ('question','style_intervention','personal_facts_intervention','fixed_context'):
        for value in (current,old):s.require(value not in c[name],'Value leak in '+name)
    s.require(current not in c['history_intervention'] and old in c['history_intervention'],'History value integrity')
    for name,text in c['diagnostic_controls'].items():
        s.require(c['speaker_name'] not in text and all(f['value'] not in text for f in c['facts']),'Control task-fact leakage')
    return {'case_id':c['case_id'],'speaker_id':c['speaker_id'],'task_family':c['family'],
        'construction_ancestor':c['construction_ancestor'],'reference_witness':witness,
        'current_value':current,'outdated_value':old,'case_validity':'VALID_WITH_LIMITATIONS_AI_ASSISTED_NOT_HUMAN_CERTIFIED',
        'S_assessment':'Instructions about lexical/register/punctuation/response form, no task fact supplied',
        'F_assessment':'Non-answer supplementary hobby/beverage facts; current/old answer identifiers absent',
        'H_assessment':'Dated old target assignment, valid historically but outdated at the current query date',
        'control_assessment':'LENGTH_MATCHED_DIAGNOSTIC_ONLY; generic document discourse may alter style/instructions/salience',
        'shared_limitations':['Synthetic authored personas; not independent human linguistic samples',
            'Shared construction ancestors and date/value scheme','First-person H attribution relies on target-persona context',
            'Question simplification changes task estimand and fidelity opportunity','Control neutrality not established']}


def make_request(c,con,configuration,parent,template,cache,serial):
    prompt=s.render(template,[{'role':'user','content':m.content(c,con,c['diagnostic_controls'].get(con))}])
    digest=s.th(prompt)
    if digest in cache:
        cached=cache[digest];s.require(cached['prompt']==prompt,'Prompt digest collision')
        ids,log=cached['ids'],cached['log'];origin='REUSED_EXACT_NATIVE_PROMPT_RECORD'
    else:
        ids,log=r.native_tokens(prompt,OUT/'native_tokenizer'/configuration/f'{serial:03d}.json',parent)
        cache[digest]={'prompt':prompt,'ids':ids,'log':log};origin='NEW_OFFLINE_NATIVE_TOKENIZATION_NO_GENERATION'
    row={'request_id':('p1_sfh_'+configuration+'_'+c['case_id']+'_'+con),
        'source_case_request_id':c['case_id']+'_'+con,'case_id':c['case_id'],'speaker_id':c['speaker_id'],
        'condition':con,'configuration_package':configuration,'family':c['family'],
        'construction_ancestor':c['construction_ancestor'],'split':c['split'],'factors':m.CELLS.get(con),
        'seed':42,'temperature':0.0,'top_p':1.0,'max_new_tokens':96,'stop':[],
        'cache_prompt':False,'ignore_eos':False,'parse_special':True,
        'messages':[{'role':'user','content':m.content(c,con,c['diagnostic_controls'].get(con))}],
        'prompt':prompt,'prompt_sha256':digest,'input_token_ids':ids,'input_tokens':len(ids),
        'input_token_ids_sha256':s.th(str(ids)),'context_remaining':4096-96-len(ids),
        'reference':c['reference'],'reference_sha256':s.th(json.dumps(c['reference'],sort_keys=True)),
        'evidence_sha256':s.th(c['trusted_evidence']),'question_sha256':s.th(c['question']),
        'context_sha256':s.th(c['fixed_context']),'evaluation_date':c['evaluation_date'],
        'requested_date':c['requested_date'],'applicability':c['applicability']}
    s.require(row['context_remaining']>0,'Context overflow')
    return row,log,origin


def prepare():
    s.require(not (OUT/'manifest_index_frozen_v1.json').exists(),'Already frozen; no regeneration')
    parent=r.validate();s.require(r.old.cumulative()['total_remaining']==88,'Budget changed')
    originals=s.load(d.OLD/'materials_v1.json')['cases']
    cases=sorted([c for c in originals if c['pool']=='factorial'],key=lambda c:c['case_id'])
    cal=[c for c in originals if c['pool']=='calibration']
    s.require(len(cases)==8 and not {c['case_id'] for c in cases}&{c['case_id'] for c in cal},'Pilot/calibration separation')
    s.require(not {c['speaker_id'] for c in cases}&{c['speaker_id'] for c in cal},'Speaker separation')
    s.require(not {c['question'] for c in cases}&{c['question'] for c in cal},'Exact question reuse')
    attempted=[s.load(p) for p in (r.old.ROOT/'attempts').glob('*.json')]
    s.require(not any(c['case_id'] in x['request_id'] for c in cases for x in attempted),'Pilot case already generated in current scope')
    fixed=s.load(fallback.OUT/'bank_frozen_v1.json')['cases'];fallback_checks=fallback.verify_bank(fixed)
    rebuilt,allocation=fallback.candidate_bank()
    s.require(all({k:v for k,v in c.items() if k!='diagnostic_controls'}=={k:v for k,v in rebuilt[i].items() if k!='diagnostic_controls'} for i,c in enumerate(fixed)),'Fallback bank/allocation changed')
    overlap=fallback.overlap_audit(fixed)
    integrity={'original_pilot_cases':[c['case_id'] for c in cases],
        'original_pilot_speakers':[c['speaker_id'] for c in cases],
        'original_family_balance':dict(Counter(c['family'] for c in cases)),
        'calibration_identity_overlap':[],'calibration_speaker_overlap':[],'calibration_exact_question_overlap':[],
        'construction_history':'All8 OQ-pilot cases already registered as development candidates in measurement_pilot_v1; zero B_FACTORIAL generations. Not new independent validation. Four task ancestors shared with calibration, reused given names, all Elmbridge surname. No pilot selection from outcomes.',
        'template_ancestors':sorted({c['construction_ancestor'] for c in cases}),
        'fallback_checks':fallback_checks,'fallback_overlap':overlap,
        'source_candidate_case_audits':[factual_audit(c) for c in cases],
        'fallback_case_audits':[factual_audit(c) for c in fixed],
        'human_material_certifications':0,'scientific_definition_corrections':[],
        'no_heldout_outputs_used':True,'controls':'DIAGNOSTIC_ONLY',
        'configuration_checks':{},'generation_requests':0}
    bundles={}
    specs={c['case_id']:d.q1(c,ordered_tie_authorized=True) for c in cases}
    for name in CONFIGS:bundles[name]=[r.v1.construct(c,name,specs[c['case_id']]) for c in cases]
    bundles['minimal_temporal']=[c for c in fixed if c['pool']=='fallback_pilot']
    s.save(OUT/'pilot_cases_by_configuration_frozen_v1.json',bundles)
    policy={'version':'p1_conditional_pilot_policy_v1','phase':'P1_ONLY_DEVELOPMENT','generation_authorized_now':False,
        'activation':'Only future explicit standalone unblind and proceed plus valid complete researcher audit',
        'selection':'Fixed OQ priority from researcher audit; one mutually exclusive pilot only. Do not execute all alternatives.',
        'case_selection':'Previously registered8 factorial cases; no outcome-based selection or family removal. Separate preallocated8 fallback pilot cases.',
        'Q1_specs':specs,'scorers':{'Q0':'Frozen tools/p1_measurement_scoring_v2.py task_success on raw answer candidate',
            'Q1':'Frozen tools/p1_recovery_design.py score_single; strict whole-response aliases only',
            'minimal_temporal':'Existing tools/p1_temporal_fallback.py endpoint CURRENT_VALUE_ADOPTION is exact task success; other categorical states preserved'},
        'gate_thresholds':{'OQ_audited_success':6,'OQ_exact_agreement':7,'fallback_automatic_calibration':7,'pilot_automatic_C0':6,'denominator':8},
        'ordering_seeds':ORDER_SEEDS,'order':'Shuffle eight C0 identities first; independently shuffle remaining72; identical package order rule, no condition-effect-based changes',
        'contrasts':contrasts(),'primary':m.policy()['primary_comparison'],
        'fallback_primary':s.load(fallback.OUT/'policy_frozen_v1.json')['primary_comparison'],
        'missingness':'Full assigned8-case denominator, signed unknown-outcome bounds; no missing-cell renormalization. A failed C0 gate leaves remaining72 ungenerated, not incorrect.',
        'statistics':'Paired case contributions, speaker IDs, whole-speaker resampling sensitivity where meaningful, task/template ancestry. No confirmatory significance or population-equivalence claims.',
        'fidelity':'Linguistic and behavioral opportunity states separate; insufficient opportunity/N/A not zero. Q1/minimal tasks cannot validate full persona fidelity.',
        'control_semantics':'Token equality is necessary length check only; procedural controls remain diagnostic.',
        'model_policy':'Original approved Instruct development configuration, no substitution, CPU4/context4096/output96/seed42',
        'automatic_gate_provenance':'Record raw scores, source hashes, threshold, decision and actual software execution time; researcher review pending. Later corrections are sidecars, not overwrites.',
        'resource_gate':'Preserve3GiB available physical RAM before loading; exact model/backend/template/live tokens and global authorization ledger mandatory.',
        'frozen_sources':{str(p):s.sha256(Path(p)) for p in [
            'tools/p1_measurement_scoring.py','tools/p1_measurement_scoring_v2.py','tools/p1_recovery_design.py',
            'tools/p1_temporal_fallback.py','tools/p1_measurement_materials.py','tools/p1_factorial_descriptive.py',
            OUT/'stage_policy_frozen_v1.json',d.OLD/'materials_v1.json',fallback.OUT/'bank_frozen_v1.json',fallback.OUT/'allocation_frozen_v1.json']}}
    s.save(OUT/'pilot_analysis_and_execution_policy_frozen_v1.json',policy)
    cache=source_token_cache();template=Path(parent['template_path']).read_text(encoding='utf-8');index={}
    originalB={x['request_id']:x for x in s.load(d.OLD/'B_FACTORIAL_manifest_v1.json')['requests']}
    for name,bank in bundles.items():
        rows=[];logs={};origins=Counter()
        for c in bank:
            for con in (*m.CELLS,'N_style','N_history'):
                row,log,origin=make_request(c,con,name,parent,template,cache,len(rows));rows.append(row);logs[row['request_id']]=log;origins[origin]+=1
                if name=='D0':s.require(row['prompt']==originalB[c['case_id']+'_'+con]['prompt'],'D0 pilot prompt changed')
        rows=ordered(rows)
        for i,row in enumerate(rows):row['order']=i;row['request_sha256']=request_hash(row)
        plan={k:parent[k] for k in SOURCE_KEYS}
        plan.update(version=('P1_minimal_temporal_SFH_pilot_v2' if name=='minimal_temporal' else 'P1_SFH_measurement_pilot_'+name+'_v2'),
            configuration_package=name,phase='P1',category='B_FACTORIAL',authorization_id=m.AUTH_ID,
            status='FROZEN_CANDIDATE_STAGE_B_ACTIVATION_REQUIRED',proposed_requests=80,maximum_executed_pilot_requests=80,
            independent_validation=False,requests=rows,native_tokenizer_logs=[logs[q['request_id']] for q in rows],
            execution_blocks={'C0_gate_request_ids':[x['request_id'] for x in rows[:8]],'conditional_remaining_request_ids':[x['request_id'] for x in rows[8:]]},
            order_seeds=ORDER_SEEDS,time_limit_minutes=60,no_retries=True,
            bound_sources={p.as_posix():s.sha256(p) for p in [OUT/'pilot_cases_by_configuration_frozen_v1.json',OUT/'pilot_analysis_and_execution_policy_frozen_v1.json',OUT/'stage_policy_frozen_v1.json']})
        audit=validate_plan(plan,bank,check_files=True)
        integrity['configuration_checks'][name]=audit|{'native_token_record_provenance':dict(origins)}
        filename=plan['version']+'.json';path=MANIFESTS/filename;s.save(path,plan)
        index[name]={'path':path.as_posix(),'sha256':s.sha256(path),'requests':80,'executed':0}
        print(json.dumps({'frozen_configuration':name,'requests':80,'native':dict(origins),'inference':0}),flush=True)
    # Existing fallback calibration is reused exactly, not rendered again.
    calpath=fallback.OUT/'fallback_calibration_manifest_candidate_v1.json'
    index['fallback_calibration']={'path':calpath.as_posix(),'sha256':s.sha256(calpath),'requests':8,'executed':0}
    s.save(OUT/'scientific_material_audit_v1.json',integrity)
    s.save(OUT/'manifest_index_frozen_v1.json',{'manifests':index,'total_candidate_requests':408,
        'maximum_new_actual_generations':88,'maximum_mutually_exclusive_branch_A':80,'maximum_mutually_exclusive_branch_B':88,
        'new_generations':0,'source_code':{str(p):s.sha256(Path(p)) for p in ['tools/p1_blinded_audit.py','tools/p1_conditional_materials.py']}})
    return {'candidate_pilots':5,'candidate_requests':408,'actual_generations':0,'mutually_exclusive_actual_maximum':88}


def validate_plan(plan,bank,check_files=True):
    rows=plan['requests'];by={c['case_id']:c for c in bank};name=plan['configuration_package']
    s.require(len(rows)==80 and len(by)==8 and len({q['request_id'] for q in rows})==80,'Pilot inventory')
    s.require([q['order'] for q in rows]==list(range(80)),'Order changed')
    s.require(all(q['condition']=='C0' for q in rows[:8]) and all(q['condition']!='C0' for q in rows[8:]),'C0 must precede72')
    s.require({q['case_id'] for q in rows[:8]}==set(by),'C0 case inventory')
    s.require(len(rows)==len(plan['native_tokenizer_logs']),'Token log inventory')
    paired=[]
    for c in bank:
        group={q['condition']:q for q in rows if q['case_id']==c['case_id']}
        s.require(set(group)==set(m.CELLS)|{'N_style','N_history'},'Factorial allocation')
        for field in ('speaker_id','evidence_sha256','question_sha256','reference_sha256','context_sha256','evaluation_date','requested_date'):
            s.require(len({q[field] for q in group.values()})==1,'Within-case invariant changed: '+field)
        for neutral,active in (('N_style','C1'),('N_history','C3')):
            s.require(group[neutral]['input_tokens']==group[active]['input_tokens'],'Actual token matching failed')
            paired.append({'case_id':c['case_id'],'active':active,'control':neutral,'tokens':group[active]['input_tokens'],'status':'DIAGNOSTIC_ONLY'})
        for con,q in group.items():
            content=q['messages'][0]['content'];before=content.split('Trusted evidence:\n')[0]
            s.require(q['messages']==[{'role':'user','content':m.content(c,con,c['diagnostic_controls'].get(con))}],'Wrong S/F/H material')
            H=bool(m.CELLS.get(con,(0,0,0))[2]);s.require((c['history_intervention'] in before)==H,'H dialogue in wrong cell')
            for i,(heading,key) in enumerate(zip(('Optional style material','Supplementary personal facts','Optional dialogue material'),('style_intervention','personal_facts_intervention','history_intervention'))):
                if con in m.CELLS:s.require((c[key] in before)==bool(m.CELLS[con][i]),'Treatment axis mismatch')
            s.require(s.th(q['prompt'])==q['prompt_sha256'] and request_hash(q)==q['request_sha256'],'Request digest')
            for key,expected in {'seed':42,'temperature':0.,'top_p':1.,'max_new_tokens':96,'stop':[],'cache_prompt':False,'ignore_eos':False,'parse_special':True}.items():s.require(q[key]==expected,'Generation parameter change')
    for q,log in zip(rows,plan['native_tokenizer_logs']):
        s.require(q['input_tokens']==len(q['input_token_ids']) and q['input_token_ids_sha256']==s.th(str(q['input_token_ids'])),'Token fields')
        s.require(q['context_remaining']==4096-96-q['input_tokens']>0,'Context capacity')
        if check_files:
            s.require(s.sha256(Path(log['path']))==log['sha256'],'Native log changed')
            n=s.load(log['path']);s.require(n['returncode']==0 and n['prompt']==q['prompt'] and ast.literal_eval(n['stdout'].strip())==q['input_token_ids'],'Native tokenizer evidence')
    return {'status':'OBJECTIVE_AND_AI_ASSISTED_CHECKS_PASS_WITH_LIMITATIONS','requests':80,'paired_cases':8,
        'actual_token_range':[min(q['input_tokens'] for q in rows),max(q['input_tokens'] for q in rows)],
        'control_pairs':paired,'independent_validation':False,'human_control_certifications':0}


def validate_all():
    idx=s.load(OUT/'manifest_index_frozen_v1.json');banks=s.load(OUT/'pilot_cases_by_configuration_frozen_v1.json')
    for path,h in idx['source_code'].items():s.require(s.sha256(Path(path))==h,'Source tool changed: '+path)
    policy=s.load(OUT/'pilot_analysis_and_execution_policy_frozen_v1.json')
    for path,h in policy['frozen_sources'].items():s.require(s.sha256(Path(path))==h,'Frozen policy/source changed: '+path)
    parent=s.load(r.MANIFEST);counts={}
    for name,ref in idx['manifests'].items():
        path=Path(ref['path']);s.require(s.sha256(path)==ref['sha256'],'Manifest changed: '+name);p=s.load(path)
        s.require(all(p[k]==parent[k] for k in SOURCE_KEYS),'Model/template/tokenizer substitution')
        for source,h in p['bound_sources'].items():s.require(s.sha256(Path(source))==h,'Bound material changed')
        if name!='fallback_calibration':validate_plan(p,banks[name]);counts[name]=80
        else:
            s.require(len(p['requests'])==8 and all(q['condition']=='C0' for q in p['requests']),'Fallback calibration inventory')
            for q,log in zip(p['requests'],p['native_tokenizer_logs']):
                s.require(s.sha256(Path(log['path']))==log['sha256'],'Fallback tokenizer changed')
                s.require(ast.literal_eval(s.load(log['path'])['stdout'].strip())==q['input_token_ids'],'Fallback token IDs')
            counts[name]=8
    s.require(sum(counts.values())==408,'Candidate scope changed')
    return {'status':'PASS_CANDIDATES_NOT_EXECUTION_AUTHORIZATION','candidate_requests':counts,'new_generations':0}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','validate']);v=p.parse_args()
    print(json.dumps(prepare() if v.action=='prepare' else validate_all(),indent=2))

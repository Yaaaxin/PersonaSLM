"""Fixed P1 fallback preparation only. Never issues a completion request.

Eight authored template families, two separate scenarios per family; all are
synthetic one-hop temporal lookup. No claim of independent human construction.
"""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random
import re
import sys
from collections import Counter

import p1_recovery_v2 as oq
import p1_recovery_design as d
from core_sfh_readiness import neutral_candidates
from personaslm_alignment import contrasts

s,m=oq.s,oq.m
OUT=oq.OUT/'fallback_bank_v1'
ALLOCATION_SEED=731901
CONSTRUCTION_SEED=731902
TEMPLATES=[
 ('library_storage','allocated locker','Locker',
  ['On {date}, which locker is allocated to {name}? Reply with one locker identifier.',
   'Give the locker allocated to {name} as of {date}. Return just one locker identifier.']),
 ('workshop_station','assigned workbench','Workbench',
  ['Which workbench should {name} use on {date}? Give a single workbench identifier.',
   'For {name}, name the assigned workbench that is valid on {date}. Supply one identifier.']),
 ('ferry_mooring','reserved berth','Berth',
  ['What is the reserved berth for {name} on {date}? Answer with one berth identifier.',
   'Identify the berth reserved for {name} at {date}. Provide one berth identifier only.']),
 ('community_garden','allocated plot','Plot',
  ['Using the dated register, give the plot allocated to {name} on {date}. One plot identifier is required.',
   'As of {date}, which garden plot belongs to {name}\'s allocation? State one plot identifier.']),
 ('archive_storage','assigned cabinet','Cabinet',
  ['Name the cabinet assigned to {name} on {date}. Give only its identifier.',
   'Which cabinet assignment applies to {name} at {date}? Return one cabinet identifier.']),
 ('music_rehearsal','booked studio','Studio',
  ['For the date {date}, what studio is booked for {name}? Give one studio identifier.',
   'Find {name}\'s booked studio valid on {date}. Respond with one studio identifier.']),
 ('volunteer_meeting','assigned meeting room','Room',
  ['Which meeting room is assigned to {name} on {date}? Supply one room identifier.',
   'On {date}, give the identifier of {name}\'s assigned meeting room. Provide a single room.']),
 ('club_storage','designated shelf','Shelf',
  ['What shelf is designated for {name} on {date}? Give exactly one shelf identifier.',
   'Report the shelf designated for {name} as of {date}. Use a single shelf identifier.'])]
NAMES=['Iona Valecrest','Merrin Oakharbor','Tessa Fairquay','Orin Larkstone','Celia Birchhaven','Nolan Reedcliff',
       'Elara Mossbridge','Perrin Westmere','Sable Thornwick','Ronan Fernshore','Livia Dawnridge','Cedric Ashcove',
       'Mara Willowfen','Tobin Rosefield','Sylva Brookmead','Dorian Pineheath']
STYLES=[
 'Use compact direct clauses and plain vocabulary. Prefer a final full stop.',
 'Use courteous complete sentences and restrained punctuation. Avoid contractions.',
 'Prefer a short declarative answer without an introductory phrase. Avoid exclamation marks.',
 'Use calm, precise wording and complete sentences. Prefer the verb identify over locate.',
 'Use economical wording and an informal conversational register. Avoid decorative imagery.',
 'Prefer formal diction and a measured sentence rhythm. Do not use slang.',
 'Use plain direct language. When several clauses are needed, separate them with semicolons.',
 'Use gentle courteous phrasing and conventional capitalization. Avoid emphatic punctuation.',
 'Keep statements concise, with one idea per sentence. Prefer everyday words.',
 'Use complete declarative sentences with a neutral professional tone. Avoid fragments when practical.',
 'Prefer brisk answers with no rhetorical questions. Use ordinary vocabulary.',
 'Use a warm but restrained register. Prefer a brief acknowledgment before an answer when both are appropriate.',
 'Use careful, literal wording and short sentences. Avoid figurative expressions.',
 'Prefer an answer followed by a brief acknowledgment when both are appropriate. Use quiet punctuation.',
 'Use a conversational yet precise register. Prefer contractions when grammatically appropriate.',
 'Use polished complete sentences without contractions. Avoid unnecessary qualifiers.']
HOBBIES=['paper folding','bird sketching','bread baking','map drawing','pottery','embroidery','chess','wood carving',
         'jigsaw puzzles','landscape painting','bookbinding','astronomy','calligraphy','weaving','stamp collecting','origami']


def candidate_bank():
    rng=random.Random(CONSTRUCTION_SEED);codes=rng.sample(range(71000,99999),100);bank=[]
    for i,name in enumerate(NAMES):
        template,attribute,kind,questions=TEMPLATES[i//2];cid=f'p1_fallback_temporal_{i:02d}'
        date=('2054-09-18','2054-10-22')[i%2];old_value=f'{kind} {codes[i*6]}';new_value=f'{kind} {codes[i*6+1]}'
        facts=[{'entity':name,'attribute':attribute,'value':old_value,'valid_from':'2054-01-01','valid_to':'2054-06-30'},
               {'entity':name,'attribute':attribute,'value':new_value,'valid_from':'2054-07-01','valid_to':'2054-12-31'}]
        for j in range(2,4+i%3):
            facts.append({'entity':f'Fictional registrant {i+101}-{j+1}','attribute':attribute,'value':f'{kind} {codes[i*6+j]}',
                          'valid_from':'2054-01-01' if j%2 else '2054-07-01','valid_to':'2054-06-30' if j%2 else '2054-12-31'})
        source_order=list(range(len(facts)));rng.shuffle(source_order)
        for f,index in zip(facts,source_order):f['source_id']=cid+f'_E{index:02d}'
        old_source,new_source=facts[0]['source_id'],facts[1]['source_id'];rng.shuffle(facts)
        question=questions[i%2].format(name=name,date=date)
        history=(f'Dated dialogue on 2054-03-20.\nUser: What was my {attribute} on that date?\n'
                 f'Speaker: My {attribute} was {old_value}.')
        bank.append({'case_id':cid,'speaker_id':f'p1_fallback_speaker_{i:02d}','speaker_name':name,
            'pool':'UNALLOCATED','split':'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION','independent_validation':False,
            'family':template,'construction_ancestor':'p1_fallback_'+template+'_v1','shared_schema_ancestor':'dated_single_attribute_lookup',
            'question_realization':i%2,'question':question,'evaluation_date':date,'requested_date':date,
            'fixed_context':'This enquiry concerns the dated register shown below. No earlier answer is assumed.',
            'facts':facts,'trusted_evidence':'\n'.join(d.evidence_line(f) for f in facts),
            'reference':[{'key':'current_value','value':new_value,'source_ids':[new_source]}],
            'old_reference':{'key':'outdated_value','value':old_value,'source_ids':[old_source]},
            'aliases':{'current':[new_value,new_value.split(' ',1)[1]],'outdated':[old_value,old_value.split(' ',1)[1]]},
            'attribute':attribute,'style_intervention':STYLES[i],
            'personal_facts_intervention':f'Name: {name}\nLeisure activity: {HOBBIES[i]}\nPreferred beverage: herbal tea',
            'history_intervention':history,'fidelity_target':{'linguistic':STYLES[i],
                'behavioral':'Not validated in this single-answer task; no behavioral fidelity claim',
                'provenance':'Individually AI-authored synthetic profile; no independent human validation'},
            'applicability':{k:'APPLICABLE' for k in ('factual','temporal','task_success','component_coverage','structural_reliability','outdated_adoption')}
                |{k:'DESCRIPTIVE_WITH_OPPORTUNITY_STATE_ONLY' for k in ('relevance','coherence','linguistic_fidelity','behavioral_fidelity')},
            'diagnostic_controls':{},'control_validity':'LENGTH_MATCHED_DIAGNOSTIC_ONLY_NOT_STRICT_NEUTRAL',
            'scientific_validity_proposal':'VALID_WITH_LIMITATIONS','researcher_validity_decision':''})
    allocation_rng=random.Random(ALLOCATION_SEED);alloc=[]
    for family in [x[0] for x in TEMPLATES]:
        pair=sorted([c for c in bank if c['family']==family],key=lambda c:c['case_id']);allocation_rng.shuffle(pair)
        for c,pool in zip(pair,('fallback_calibration','fallback_pilot')):c['pool']=pool;alloc.append({'case_id':c['case_id'],'speaker_id':c['speaker_id'],'family':family,'pool':pool})
    return bank,alloc


def overlap_audit(bank):
    # Read construction inventories, not held-out model outputs. Shared schema
    # is disclosed; exact identity separation is not template independence.
    paths=list(Path('data/synthetic').glob('*.json'))+[Path('data/synthetic/p0_cases.jsonl'),
        d.OLD/'materials_v1.json',s.b.DEV/'development_examples_v5.json',
        Path('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')]
    seen={k:set() for k in ('case_id','speaker_id','speaker_name','question')}
    def walk(v):
        if isinstance(v,dict):
            for k in seen:
                if isinstance(v.get(k),str):seen[k].add(v[k])
            for item in v.values():walk(item)
        elif isinstance(v,list):
            for item in v:walk(item)
    sources={}
    for path in paths:
        if not path.exists():continue
        sources[path.as_posix()]=s.sha256(path)
        if path.suffix=='.jsonl':
            for line in path.read_text(encoding='utf-8').splitlines():
                if line.strip():walk(json.loads(line))
        else:walk(s.load(path))
    overlaps={k:sorted({c[k] for c in bank}&v) for k,v in seen.items()}
    s.require(not any(overlaps.values()),'Fallback identity/question overlap')
    return {'sources':sources,'exact_overlap':overlaps,'historical_counts':{k:len(v) for k,v in seen.items()},
        'scope':'Construction inventories only; no held-out outputs inspected. Eight distinct authored templates share a single temporal-lookup schema; not independent linguistic population sampling.'}


def verify_bank(bank):
    s.require(len(bank)==16 and len({c['case_id'] for c in bank})==len({c['speaker_id'] for c in bank})==16,'Bank inventory')
    s.require(Counter(c['pool'] for c in bank)=={'fallback_calibration':8,'fallback_pilot':8},'Allocation count')
    for c in bank:
        s.require(4<=len(c['facts'])<=6,'Evidence count');d.reference_audit(c)
        targets=[f for f in c['facts'] if f['entity']==c['speaker_name'] and f['attribute']==c['attribute']]
        s.require(len(targets)==2,'Expected one old and one current target record')
        current=[f for f in targets if f['valid_from']<=c['requested_date']<=f['valid_to']]
        s.require(len(current)==1 and current[0]['value']==c['reference'][0]['value'],'Non-unique current answer')
        outdated=next(f for f in targets if f['value']==c['old_reference']['value'])
        s.require(outdated['valid_to']<c['requested_date'] and outdated['valid_from']<='2054-03-20'<=outdated['valid_to'],'Stale/history scope')
        for label in ('current','outdated'):
            s.require(len(set(d.normalize_single(v) for v in c['aliases'][label]))==2,'Alias collision')
        for value in (current[0]['value'],outdated['value']):
            s.require(all(value not in c[k] for k in ('question','style_intervention','personal_facts_intervention','fixed_context')),'Answer leakage')
        s.require(current[0]['value'] not in c['history_intervention'] and outdated['value'] in c['history_intervention'],'H content')
    return {'objective_validity_checks':'PASS','AI_validity_proposals':16,'human_confirmations':0,
        'templates':8,'shared_schema_ancestors':1,'profiles':16,'independent_human_authors':0,
        'allocation_seed':ALLOCATION_SEED,'one_case_per_template_per_pool':True}


def endpoint(text,c):
    """Conservative outcome categories; never equates unknown with stale."""
    if text is None:return 'MISSING_RECORD'
    norm=d.normalize_single(text)
    if not norm:return 'EMPTY_RESPONSE'
    for label in ('current','outdated'):
        if norm in {d.normalize_single(v) for v in c['aliases'][label]}:return label.upper()+'_VALUE_ADOPTION'
    for f in c['facts']:
        if f['entity']!=c['speaker_name'] and norm in {d.normalize_single(f['value']),d.normalize_single(f['value'].split(' ',1)[1])}:return 'WRONG_ENTITY_ANSWER'
    # Only list-like unnegated multiple identifiers have an automatic conflict
    # flag. Prose with negation/historical attribution remains unverified.
    current=c['aliases']['current'];old=c['aliases']['outdated']
    if any(norm==d.normalize_single(a+sep+b) or norm==d.normalize_single(b+sep+a) for a in current for b in old for sep in (', ','; ',' and ',' or ')):
        return 'CONTRADICTORY_ANSWER_REQUIRES_REVIEW'
    return 'UNVERIFIABLE_ANSWER'


def prepare():
    s.require(not (OUT/'bank_frozen_v1.json').exists(),'Preserve fixed fallback bank')
    parent=oq.validate();bank,allocation=candidate_bank();checks=verify_bank(bank);overlap=overlap_audit(bank)
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    template=Path(parent['template_path']).read_text(encoding='utf-8')
    render=lambda c,con,neutral=None:s.render(template,[{'role':'user','content':m.content(c,con,neutral)}])
    # Vocabulary-only length search; no model-output-guided prompt tuning.
    extra=['The printed document contains '+a+' '+b+' '+c+' '+where+'.'
        for a,b,c,where in itertools.product(('some','several','a few'),('short','ordinary','clearly separated','plain'),
            ('sentences','paragraphs','descriptive passages'),('on the page','under a heading','within the same printed section','in this section'))]
    extra += [base+' '+ending for base in list(extra) for ending in
        ('A heading is visible.','One short title is visible.','Several headings separate the paragraphs.')]
    candidates=list(neutral_candidates())+extra;controls=[]
    for c in bank:
        if c['pool']!='fallback_pilot':continue
        for con,active in (('N_style','C1'),('N_history','C3')):
            want=len(tok.encode(render(c,active),add_special_tokens=True).ids)
            match=next((text for text in candidates if len(tok.encode(render(c,con,text),add_special_tokens=True).ids)==want),None)
            s.require(match is not None,'No exact tokenizer-matched procedural control: '+c['case_id']+' '+con)
            c['diagnostic_controls'][con]=match
            controls.append({'case_id':c['case_id'],'control':con,'active':active,'tokens':want,
                'status':'LENGTH_MATCHED_DIAGNOSTIC_ONLY','semantic_risks':['Formatting instructions/descriptions','Topic and discourse change','No proof of semantic neutrality']})
    policy={'version':'fixed_minimal_temporal_fallback_policy_v1','phase':'P1_ONLY','inference_activated':False,
        'source':'Explicit current user sections8-14','primary_comparison':'C3-C0 outdated-answer adoption incidence',
        'eligible_cases':[c['case_id'] for c in bank if c['pool']=='fallback_pilot'],'denominator':8,
        'definitions':{'current':'Affirmative target-attribute answer valid at registered query date',
            'outdated':'Affirmative old target value assigned to current query; correctly scoped historical mention alone is not adoption',
            'wrong_entity':'An answer belonging to another entity in the evidence',
            'unverifiable':'Unsupported/unresolved assertion or outside frozen automatic grammar; not coded as outdated',
            'missing':'No record; separate from observed empty reply','contradictory':'Multiple incompatible values asserted for same current target; review negation and temporal scope'},
        'normalization':'Same NFKC/whitespace/casefold/single-terminal-period rule as Q1; exact full-answer aliases frozen.',
        'unknown_handling':'Report full category distribution, full8 denominator and unknown identification bounds; never code missing/unverifiable as observed outdated.',
        'reliability_endpoints':'Separate factual, temporal, task and component support; no composite',
        'fidelity_scope':'Single-answer tasks cannot independently validate linguistic/behavioral fidelity or coherence; unavailable opportunity is not zero.',
        'Q0_calibration_activation':['OQ24 complete','Researcher-confirmed32-label snapshot','No OQ condition qualifies','Bank and preflight pass'],
        'fallback_qualifies':'Researcher-confirmed calibration success>=7/8; prepare qualified pilot v2 only, do not execute80.',
        'fallback_fails':'Stop; formal model-feasibility/model-selection review; no prompt variants or P3 inference.',
        'later_pilot':'Separate authorization; eight C0 first, audited>=6/8 to continue72; no substitutions.',
        'statistical_scope':'Eight paired purposive synthetic cases, shared template/schema dependencies; descriptive development, no population/confirmatory claims',
        'factorial_contrasts':contrasts(),'control_status':'DIAGNOSTIC_ONLY'}
    s.save(OUT/'policy_frozen_v1.json',policy)
    s.save(OUT/'allocation_frozen_v1.json',{'seed':ALLOCATION_SEED,'algorithm':'Python Random(seed); fixed template order, sort two case IDs then shuffle each pair; first calibration, second pilot',
        'construction_seed':CONSTRUCTION_SEED,'assignments':allocation,'outcomes_inspected':False,'reallocation_allowed':False})
    s.save(OUT/'bank_frozen_v1.json',{'cases':bank,'maintainer':'Yaxin ZHENG','constructed_utc':s.b.utc_now(),
        'provenance':'AI-authored synthetic development scenarios/profiles with recorded construction ancestry; not independently human-validated'})
    s.save(OUT/'validity_and_overlap_v1.json',checks|{'overlap':overlap,'control_pairs':controls})
    groups={'fallback_calibration':[],'fallback_pilot':[]};logs={k:[] for k in groups}
    for c in bank:
        cons=['C0'] if c['pool']=='fallback_calibration' else [*m.CELLS,'N_style','N_history']
        for con in cons:
            text=m.content(c,con,c['diagnostic_controls'].get(con));prompt=s.render(template,[{'role':'user','content':text}]);group=c['pool'];order=len(groups[group])
            ids,log=oq.native_tokens(prompt,OUT/'native_tokenizer'/group/f'{order:03d}.json',parent)
            row={'request_id':c['case_id']+'_'+con,'case_id':c['case_id'],'speaker_id':c['speaker_id'],'condition':con,
                'family':c['family'],'factors':m.CELLS.get(con),'split':c['split'],'order':order,'seed':42,'temperature':0.,'top_p':1.,
                'max_new_tokens':96,'stop':[],'ignore_eos':False,'cache_prompt':False,'parse_special':True,
                'messages':[{'role':'user','content':text}],'prompt':prompt,'prompt_sha256':s.th(prompt),
                'input_token_ids':ids,'input_tokens':len(ids),'input_token_ids_sha256':s.th(str(ids)),'context_remaining':4096-96-len(ids),
                'reference':c['reference'],'reference_sha256':s.th(json.dumps(c['reference'],sort_keys=True)),
                'evidence_sha256':s.th(c['trusted_evidence']),'question_sha256':s.th(c['question']),
                'context_sha256':s.th(c['fixed_context']),'evaluation_date':c['evaluation_date'],'applicability':c['applicability']}
            s.require(row['context_remaining']>0,'Context capacity');row['request_sha256']=s.th(json.dumps(row,sort_keys=True,separators=(',',':')))
            groups[group].append(row);logs[group].append(log)
    for group,rows in groups.items():
        plan={k:parent[k] for k in ('model','template_path','template_sha256','native_tokenizer_identity','decoding_policy','candidate_metadata_sha256')}
        plan.update(version=group+'_manifest_candidate_v1',phase='P1',category='C_DIAGNOSTIC' if group=='fallback_calibration' else 'B_FACTORIAL',
            authorization_id=m.AUTH_ID,requests=rows,proposed_requests=len(rows),native_tokenizer_logs=logs[group],independent_validation=False,
            status='CONDITIONAL_AUTHORIZATION_NOT_ACTIVATED' if group=='fallback_calibration' else 'PREPARED_CANDIDATE_NOT_QUALIFIED_NOT_AUTHORIZED',
            bound_sources={p.as_posix():s.sha256(p) for p in [OUT/'bank_frozen_v1.json',OUT/'allocation_frozen_v1.json',OUT/'policy_frozen_v1.json']})
        s.save(OUT/(group+'_manifest_candidate_v1.json'),plan)
    # Full-prompt equality, not approximate block-length matching.
    pilot=groups['fallback_pilot']
    for c in bank:
        if c['pool']!='fallback_pilot':continue
        rs={r['condition']:r for r in pilot if r['case_id']==c['case_id']}
        for field in ('evidence_sha256','question_sha256','reference_sha256','context_sha256','evaluation_date','speaker_id'):
            s.require(len({r[field] for r in rs.values()})==1,'Paired invariant changed')
        for control,active in (('N_style','C1'),('N_history','C3')):s.require(rs[control]['input_tokens']==rs[active]['input_tokens'],'Native control mismatch')
    s.save(OUT/'manifest_bindings_v1.json',{g:s.sha256(OUT/(g+'_manifest_candidate_v1.json')) for g in groups})
    return {'cases':16,'calibration_candidates':8,'pilot_candidates':80,'native_tokenizer_checks':88,'control_pairs':16,'new_generations':0,'activation':'PENDING_OQ_COMPLETION_AND_RESEARCHER_AUDIT'}


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(prepare(),indent=2))

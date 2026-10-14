"""Known-method engineering baseline: dated structured claims, not a new algorithm.

Authored fixtures only. No language-to-claim extraction, model inference or official
semantic labels. Claim validity and requested-answer delivery are distinct.
"""
import copy
from datetime import date
from pathlib import Path
import statistics
import time
from p1d_design import read, write, csvwrite, sha, lookup
from p1d_offline_baselines import verify_structured, fixtures

DEST = Path('docs/validation/p1d/development_readiness_v1/verifier_date_scope_v1')

def check(payload, facts, query, use_claim_time=True, enforce_unique=True, check_delivery=True):
    labels, details, supported = [], [], set()
    for claim in payload['assertions']:
        # Explicitly unresolved extraction is never coerced into a factual error.
        when = claim.get('claim_date', query['date']) if use_claim_time else query['date']
        if claim.get('extraction_uncertain') or when is None:
            labels.append('Unverifiable'); details.append({'status': 'Unverifiable', 'reason': 'EXTRACTION_OR_DATE_UNRESOLVED'}); continue
        try:
            date.fromisoformat(when)
        except (TypeError, ValueError):
            labels.append('Unverifiable'); details.append({'status': 'Unverifiable', 'reason': 'INVALID_DATE'}); continue
        candidates = [f for f in facts if f['entity']==claim['entity'] and f['predicate']==claim['predicate'] and f['start']<=when<=f['end']]
        values = {f['value'] for f in candidates}
        if not candidates or (enforce_unique and len(values)!=1):
            status = 'Unverifiable'; reason = 'NO_SUPPORT' if not candidates else 'CONFLICTING_TRUSTED_EVIDENCE'
        else:
            match = claim['value'] in values
            if claim.get('negated'):
                match = not match
            status = 'Correct' if match else 'Incorrect'; reason = 'EXPLICIT_ENTITY_ATTRIBUTE_DATE_CHECK'
        labels.append(status)
        details.append({'status': status, 'reason': reason, 'claim_date': when, 'source_ids': [f['id'] for f in candidates]})
        if status=='Correct' and not claim.get('negated') and when==query['date'] and claim['entity']==query['entity']:
            supported.add(claim['predicate'])
    factual = 'Incorrect' if 'Incorrect' in labels else 'Unverifiable' if not labels or 'Unverifiable' in labels else 'Correct'
    coverage = len(supported & set(query['required_predicates']))/len(query['required_predicates'])
    delivery = payload['speech_act']=='answer' if check_delivery else True
    return {'factual': factual, 'supported_component_fraction': coverage,
        'task_success': delivery and coverage==1 and factual=='Correct', 'claims': details,
        'abstain_from_full_certification': factual=='Unverifiable',
        'scope': 'Single-valued structured predicates with explicit date attribution; no free-text scoring or empirical reliability claim'}

def challenge_bank(case):
    bank = fixtures(case)
    for r in bank:
        r['facts'] = case['facts']
    q = copy.deepcopy(bank[0]['query'])
    old = [dict(c, value=lookup(case['facts'],q['entity'],c['predicate'],'2048-01-15')['value'], claim_date='2048-01-15') for c in bank[0]['payload']['assertions']]
    # Pickup windows are also dated; legitimate old claims do not answer the current query.
    extras = [
        ('true_explicit_historical_answer', {'assertions': old, 'speech_act':'answer'}, case['facts'], 'Correct', False),
        ('current_values_falsely_dated_old', {'assertions': [dict(c, claim_date='2048-01-15') for c in bank[0]['payload']['assertions']], 'speech_act':'answer'}, case['facts'], 'Incorrect', False),
        ('unresolved_claim_date', {'assertions': [dict(c, claim_date=None) for c in bank[0]['payload']['assertions']], 'speech_act':'answer'}, case['facts'], 'Unverifiable', False),
        ('uncertain_extraction', {'assertions': [dict(c, extraction_uncertain=True) for c in bank[0]['payload']['assertions']], 'speech_act':'answer'}, case['facts'], 'Unverifiable', False),
    ]
    conflict = copy.deepcopy(case['facts'])
    original = lookup(conflict,q['entity'],'locker',q['date'])
    conflict.append(dict(original, id='AUTHORED_CONFLICT', value='Locker 999'))
    extras.append(('conflicting_trusted_interval', copy.deepcopy(bank[0]['payload']), conflict, 'Unverifiable', False))
    for name,payload,facts,fc,success in extras:
        bank.append({'id':name,'query':q,'payload':payload,'facts':facts,'authored_expected_factual':fc,
            'authored_expected_success':success,'provenance':'AUTHORED_SOFTWARE_FIXTURE_NOT_MODEL_RESPONSE_OR_HUMAN_RATING'})
    return bank

def run():
    case = read('docs/validation/p1d/proposed_v1/development_examples_v3.json')['cases'][0]
    bank = challenge_bank(case); records = []
    methods = {'original_query_date_only': lambda p,f,q:verify_structured(p,f,q),
               'claim_date_scope': lambda p,f,q:check(p,f,q),
               'without_claim_date': lambda p,f,q:check(p,f,q,use_claim_time=False),
               'without_unique_support': lambda p,f,q:check(p,f,q,enforce_unique=False),
               'without_delivery': lambda p,f,q:check(p,f,q,check_delivery=False)}
    for fixture in bank:
        for name,fn in methods.items():
            result=fn(fixture['payload'],fixture['facts'],fixture['query'])
            records.append({'fixture_id':fixture['id'],'method':name,**result,
                'matches_authored_spec': result['factual']==fixture['authored_expected_factual'] and result['task_success']==fixture['authored_expected_success']})
    cpu=[]
    for _ in range(7):
        start=time.process_time_ns()
        for _ in range(300):
            for f in bank:check(f['payload'],f['facts'],f['query'])
        cpu.append((time.process_time_ns()-start)/(300*len(bank)))
    write(DEST/'authored_challenges_v1.json',bank);csvwrite(DEST/'comparison_v1.csv',records)
    summary={'fixtures':len(bank),'matches':{m:sum(r['matches_authored_spec'] for r in records if r['method']==m) for m in methods},
        'median_process_cpu_ns_per_check':statistics.median(cpu),'cpu_batches_ns':cpu,'new_generations':0,
        'independent_accuracy':None,'persona_fidelity_effect':None,'free_text_extraction_validated':False,
        'classification':'ENGINEERING_CORRECTION_OF_KNOWN_STRUCTURED_VERIFICATION',
        'observed_issue':'Prior baseline used requested date for every claim, even explicitly dated historical statements; unknown dates and conflicting sources were not represented.',
        'prior_art_overlap':'Temporal query/evidence filtering (LongMemEval); independent fact verification (CoVe); evidence-supported revision (RARR). This is not reproduction of their full systems.',
        'methodological_gap_demonstrated_against_published_methods':False,
        'source_sha256':sha(__file__),'old_baseline_sha256':sha('tools/p1d_offline_baselines.py'),
        'dataset_sha256':sha('docs/validation/p1d/proposed_v1/development_examples_v3.json')}
    write(DEST/'summary_v1.json',summary);print(summary)

if __name__=='__main__':
    run()

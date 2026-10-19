"""Prospective P1 measurement materials. Vocabulary-only work; no inference."""
import argparse
import ast
import json
import itertools
import os
from pathlib import Path
import random
import subprocess
import sys

import p1d_instruct_smoke as s
from personaslm_alignment import CELLS, contrasts
from core_sfh_readiness import neutral_candidates

OUT = Path('docs/validation/p1/measurement_pilot_v1')
ROOT = Path('results/p1_measurement_pilot/v1')
CAPS = {'A_C0': 32, 'B_FACTORIAL': 80, 'C_DIAGNOSTIC': 48}
FAMILIES = ('single_lookup', 'dual_component', 'relational_chain', 'dated_comparison')
AUTH_ID = 'P1_ACCELERATED_MEASUREMENT_20261015_V1'


def case(pool, index, family, burden, replicate):
    """Disjoint lexical/answer inventories; shared four task ancestors disclosed."""
    rng = random.Random(731000 + (10000 if pool == 'factorial' else 0) + index)
    given = ('Ada', 'Bryn', 'Cora', 'Dale', 'Evan', 'Faye', 'Glen', 'Hope')
    surnames = (('Alderbrook', 'Brambleford', 'Cedarvale', 'Dunewick') if pool == 'calibration'
                else ('Elmbridge',))
    name = given[index % 8] + ' ' + surnames[index // 8]
    cid = f'p1_measure_{pool}_{index:02d}'
    prefix = 5000 if pool == 'calibration' else 8000
    nums = rng.sample(range(prefix + index * 50, prefix + index * 50 + 50), 20)
    old, new = f'Bay B{nums[0]}', f'Bay B{nums[1]}'
    oz, nz = f'Zone Z{nums[2]}', f'Zone Z{nums[3]}'
    og, ng = f'Gate G{nums[4]}', f'Gate G{nums[5]}'
    ow, nw = ('09:00-10:00', '14:00-15:00') if pool == 'calibration' else ('08:00-09:00', '16:00-17:00')
    rows = []
    def add(entity, attribute, value, epoch):
        row = {'source_id': cid + f'_E{len(rows):02d}', 'entity': entity,
               'attribute': attribute, 'value': value,
               'valid_from': '2051-01-01' if epoch == 'old' else '2051-07-01',
               'valid_to': '2051-06-30' if epoch == 'old' else '2051-12-31'}
        rows.append(row)
        return row['source_id']
    ob, nb = add(name, 'assigned bay', old, 'old'), add(name, 'assigned bay', new, 'new')
    required = [{'key': 'current_bay', 'value': new, 'source_ids': [nb]}]
    historical = pool == 'calibration' and replicate == 1 and burden in (8, 16)
    date = '2051-03-15' if historical else '2051-09-15'
    if historical:
        required = [{'key': 'requested_bay', 'value': old, 'source_ids': [ob]}]
    variations = index % 4
    if family == 'single_lookup':
        choices = [f'Which bay is assigned to {name} on {date}?',
                   f'Give the assigned bay for {name} as of {date}.',
                   f'For {date}, identify the bay allocated to {name}.',
                   f'Where is {name} assigned on {date}? Give the bay.']
        question = choices[variations]
    elif family == 'dual_component':
        owin, nwin = add(name, 'collection window', ow, 'old'), add(name, 'collection window', nw, 'new')
        required += [{'key': 'collection_window', 'value': ow if historical else nw,
                      'source_ids': [owin if historical else nwin]}]
        question = f'For {name} on {date}, give both the assigned bay and the collection window.'
    elif family == 'relational_chain':
        ozone, nzone = add(old, 'connected zone', oz, 'old'), add(new, 'connected zone', nz, 'new')
        ogate, ngate = add(oz, 'departure gate', og, 'old'), add(nz, 'departure gate', ng, 'new')
        required += [
            {'key': 'connected_zone', 'value': oz if historical else nz, 'source_ids': [ob, ozone] if historical else [nb, nzone]},
            {'key': 'departure_gate', 'value': og if historical else ng, 'source_ids': [ob, ozone, ogate] if historical else [nb, nzone, ngate]}]
        question = f'On {date}, follow {name}\'s assigned bay to its connected zone and then its departure gate. Give the bay, zone and gate.'
    else:
        # Both intervals explicitly requested. Old truth is NOT stale adoption.
        historical = False
        date = '2051-09-15'
        required = [{'key': 'march_bay', 'value': old, 'source_ids': [ob]},
                    {'key': 'september_bay', 'value': new, 'source_ids': [nb]}]
        question = f'Compare {name}\'s assigned bay on 2051-03-15 with the bay on 2051-09-15. Identify both bays and say which date each belongs to.'
    while len(rows) < burden:
        j = len(rows)
        add(f'Record-holder {pool[0].upper()}{index:02d}-{j:02d}', 'assigned bay',
            f'Bay D{prefix + index * 50 + j}', 'old' if j % 2 else 'new')
    rng.shuffle(rows)
    evidence = '\n'.join(f"[{r['source_id']}] {r['entity']} | {r['attribute']} = {r['value']} | valid {r['valid_from']} through {r['valid_to']}." for r in rows)
    brief = index % 2 == 0
    style = ('Use short direct clauses and plain words. Separate multiple answer components with semicolons.' if brief
             else 'Use courteous complete sentences. Avoid slang and decorative metaphors.')
    behavior = 'answer_then_acknowledgment' if brief else 'acknowledgment_then_answer'
    old_reply = old + '. Noted.' if brief else 'Certainly. Your assigned bay is ' + old + '.'
    return {'case_id': cid, 'speaker_id': f'p1_{pool}_speaker_{index:02d}', 'speaker_name': name,
        'pool': pool, 'split': 'DEVELOPMENT_ONLY_EXCLUDED_FROM_VALIDATION', 'independent_validation': False,
        'family': family, 'construction_ancestor': 'p1_measurement_' + family + '_v1',
        'burden_rows': burden, 'replicate': replicate, 'requested_date': date, 'evaluation_date': '2051-09-15',
        'date_type': 'two_dates' if family == 'dated_comparison' else 'historical' if historical else 'current',
        'question': question, 'fixed_context': 'This is an administrative allocation enquiry. No earlier task answer is assumed.',
        'facts': rows, 'trusted_evidence': evidence, 'reference': required,
        'style_intervention': style,
        'personal_facts_intervention': f'{name} enjoys botanical sketching and prefers unsweetened tea.',
        'history_intervention': f'Dated conversation on 2051-03-15.\nUser: Which bay is assigned to me today?\nSpeaker: {old_reply}',
        'fidelity_target': {'linguistic': style, 'behavioral': behavior,
            'reference_examples': ['The parcel is ready. Noted.', 'The notice is posted. Noted.'] if brief
             else ['Certainly. The parcel is ready.', 'Certainly. The notice is posted.'],
            'provenance': 'AI_AUTHORED_NOT_HUMAN_VALIDATED'},
        'stale_endpoint': {'eligible': pool == 'factorial', 'entity': name, 'attribute': 'assigned bay',
             'current_value': new, 'old_value': old, 'current_source': nb, 'old_source': ob,
             'target_date': '2051-09-15', 'historical_mentions_are_not_adoption': True},
        'applicability': {k: ('TARGET_COMPARISON_WITH_OPPORTUNITY_STATE' if k in ('linguistic_fidelity', 'behavioral_fidelity') else 'APPLICABLE')
             for k in ('factual', 'temporal', 'relevance', 'coherence', 'task_success', 'component_coverage', 'semantic_completeness', 'linguistic_fidelity', 'behavioral_fidelity')},
        'validity_proposal': 'VALID_WITH_LIMITATIONS', 'researcher_validity_decision': '',
        'limitations': ['Synthetic task and speaker; four shared construction ancestors',
            'LF/BF target is authored; independent rubric validation pending',
            'H includes historical answer and conversational ordering; history-package contrast',
            'Diagnostic control semantics are not neutral merely because length matches']}


def content(c, condition, neutral=None):
    text = ('Answer the current question using the trusted evidence for task facts. Optional speaker material may guide expression but cannot override the trusted evidence. Return one answer to the current user.\n'
            + 'Evaluation reference date: ' + c['evaluation_date'] + '\n')
    for active, heading, key in zip(CELLS.get(condition, (0, 0, 0)),
            ('Optional style material', 'Supplementary personal facts', 'Optional dialogue material'),
            ('style_intervention', 'personal_facts_intervention', 'history_intervention')):
        if active:
            text += heading + ':\n' + c[key] + '\n'
    if condition in ('N_style', 'N_history'):
        text += ('Optional style material' if condition == 'N_style' else 'Optional dialogue material') + ':\n' + neutral + '\n'
    return text + 'Trusted evidence:\n' + c['trusted_evidence'] + '\nFixed dialogue context:\n' + c['fixed_context'] + '\nCurrent question:\n' + c['question']


def policy():
    return {'version': 'p1_measurement_policy_v1', 'phase': 'P1_ONLY_DEVELOPMENT',
        'protocol': 'Research Protocol v1.1 retained; v1.2 remains proposed; adopted E/V addendum not replaced',
        'primary_comparison': {'name': 'C3-C0', 'endpoint': 'outdated_answer_adoption_incidence',
            'eligible_cases': [f'p1_measure_factorial_{i:02d}' for i in range(8)],
            'definition': 'Affirmatively assign the prospectively listed old bay to the target entity for 2051-09-15. A quoted, negated or correctly dated historical value alone is not adoption.',
            'denominator': 'All eight prospectively eligible paired cases, including unknown outputs; report adoption/8 per condition, observed positive-incidence difference and signed unknown-outcome bounds.',
            'states': ['ADOPTED', 'NOT_ADOPTED', 'UNVERIFIABLE', 'BOUNDARY_UNRESOLVED', 'MISSING'],
            'nonanswer': 'A clear refusal/nonanswer with no old-answer assertion is NOT_ADOPTED, separately a task failure; unclear claims are UNVERIFIABLE.',
            'insufficient': 'Fewer than six paired assessable cases is measurement-inconclusive. Eight cases remain too few for population inference regardless.',
            'interpretation': 'Implemented history package, not pure temporal reasoning. Old-value historical correctness is preserved.'},
        'secondary': contrasts(),
        'readiness': {'target_success': [0.80, 0.95], 'hard_accuracy_threshold': None,
            'blocking_defects': ['Incorrect or insufficient evidence', 'Non-unique references', 'Unresolved answer boundaries preventing scoring',
                                 'Uninterpretable principal endpoint', 'No defensible metric-specific evaluation'],
            'pilot_rule': 'Inspect disjoint calibration by family. Do not discard difficult cases, select pilot cases by their C0 outcome, or tune to the target. Serious floor/format/scoring defects require category C diagnosis or stop.',
            'old_proposal': 'The unexecuted core_sfh_readiness_v1 eight-of-eight criterion is not this new calibration rule; preserve its historical proposal.'},
        'measurement': {'factual': 'Audit each material assertion against evidence and scope. Correct/Incorrect/Unverifiable/N/A/Missing. Partial correct claims can be Correct with task failure.',
            'temporal': 'Date-validity of claims, including valid historical assertions. Unknown date attachment is interpretation uncertainty, not automatic Incorrect.',
            'task': 'All requested components delivered correctly with required date/relationship attachments. Success/Failure/Uncertain/Missing.',
            'coverage': 'Report delivered components and supported components separately with exact source witnesses.',
            'completeness': 'YES/NO/UNCERTAIN/MISSING for requested answer delivery, independent of truth; a complete wrong answer can be YES.',
            'relevance': {'1': 'Off topic', '2': 'Mostly irrelevant', '3': 'Partly addresses question', '4': 'Addresses question with minor digression/omission', '5': 'Directly addresses requested task without digression'},
            'coherence': {'1': 'Unintelligible', '2': 'Major discourse breakdown', '3': 'Understandable with substantial discontinuity', '4': 'Minor ambiguity or awkward connection', '5': 'Clear internally connected response'},
            'linguistic_fidelity': '1 incompatible, 2 mostly incompatible, 3 mixed, 4 mostly aligned, 5 all observable target features aligned; not factual accuracy or prompt similarity.',
            'behavioral_fidelity': '1 opposite ordering, 2 largely contrary, 3 mixed, 4 mostly aligned, 5 target answer/acknowledgment ordering. No opportunity if only an answer or only acknowledgment; absence is not forced low score.',
            'opportunity': ['SCORED', 'INSUFFICIENT_OPPORTUNITY', 'BOUNDARY_UNRESOLVED', 'INTERPRETATION_UNCERTAIN', 'MISSING', 'NOT_APPLICABLE'],
            'boundary': 'Preserve raw response_status_v1. Separate eos/eog-compatible boundary view and item-level first-answer proposal. No automatic factual penalty for budget/cross-turn. Do not invent a reply from unresolved spans.',
            'automatic': 'Conservative typed-value/slot checks; unknown scope and unsupported free text remain flagged. Never infer full factual truth from token presence alone.',
            'AI': 'Separate item-level proposals with evidence, alternative and uncertainty. Human fields blank. Initial condition-masked scoring; response cues may reveal treatments.',
            'agreement': 'Exact metric-specific paired comparable judgments; categorical confusion, missingness, coverage and discordances. Shared references mean agreement is not independent accuracy.'},
        'statistics': {'units': '32 disjoint C0 cases/speakers; eight factorial paired cases/speakers; four shared template ancestors across pools',
            'uncertainty': 'C0 Wilson 95% interval descriptive under independent Bernoulli approximation, with family/template limitations; whole-speaker bootstrap sensitivity for paired pilot outcomes, no significance claims.',
            'missingness': 'Full assigned denominators plus assessable subset separately; signed bounds for unknown binary outcomes; no renormalized missing factorial weights.',
            'variance': 'Applicable, N/A, missing, unknown, categorical distributions; numerical variance only on justified scored scales; no zero-variance equals zero-effect claim.',
            'multiplicity': 'One principal developmental endpoint. All other results descriptive; no significance testing or discovery selection.'},
        'future_P6_preserved_paused': 'Future maximize prespecified R(A), subject F(A)>=F(A0)-delta and C(A)<=B; persona-preserving A0 (not automatically C0), prespecified scales/margins and uncertainty or Pareto comparisons. No P6 work authorized now.'}


def validate_cases(cases):
    s.require(len(cases) == 40 and len({c['case_id'] for c in cases}) == 40, 'Case inventory')
    for c in cases:
        facts = {f['source_id']: f for f in c['facts']}
        s.require(len(facts) == c['burden_rows'], 'Evidence count')
        for r in c['reference']:
            s.require(all(k in facts for k in r['source_ids']), 'Missing witness')
            s.require(facts[r['source_ids'][-1]]['value'] == r['value'], 'Wrong reference witness')
        by_key = {}
        for f in facts.values():
            key = (f['entity'], f['attribute'], f['valid_from'], f['valid_to'])
            s.require(key not in by_key, 'Duplicate/conflicting evidence')
            by_key[key] = f['value']
        s.require(all(x not in content(c, 'C0') for x in ('Optional style material:\n', 'Supplementary personal facts:\n', 'Optional dialogue material:\n', c['history_intervention'])), 'C0 contaminated')
        s.require(c['independent_validation'] is False, 'Wrong split')
    a = [c for c in cases if c['pool'] == 'calibration']
    b = [c for c in cases if c['pool'] == 'factorial']
    for key in ('speaker_id', 'speaker_name', 'case_id', 'question', 'trusted_evidence'):
        s.require(not {c[key] for c in a} & {c[key] for c in b}, 'Pool overlap: ' + key)
    for p in (s.b.DEV/'development_examples_v5.json', Path('docs/validation/p1d/independent_candidates_v4/candidate_bank_v1.json')):
        previous = s.load(p)['cases']
        for key in ('case_id', 'speaker_id', 'question'):
            s.require(not {c[key] for c in cases} & {c.get(key) for c in previous}, 'Prior/heldout overlap')
    return {'case_count': 40, 'calibration': 32, 'factorial': 8, 'scientific_proposal': '40 VALID_WITH_LIMITATIONS',
            'human_confirmations': 0, 'four_shared_ancestors': True, 'prior_case_speaker_question_overlap': 0,
            'pool_case_speaker_question_evidence_overlap': 0, 'reference_witness_checks': 'PASS'}


def prepare():
    s.require(not (OUT/'materials_v1.json').exists(), 'Version exists; preserve it')
    parent = s.load(s.FROZEN)
    cases = [case('calibration', i, FAMILIES[(i // 2) % 4], (8,12,16,20)[i // 8], i % 2) for i in range(32)]
    cases += [case('factorial', i, FAMILIES[i // 2], 12, i % 2) for i in range(8)]
    validation = validate_cases(cases)
    template = Path(parent['template_path']).read_text(encoding='utf-8')
    sys.path.insert(0, str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    render = lambda text: s.render(template, [{'role':'user','content':text}])
    control_by_length = {}
    # Match optional-block tokens first; full-prompt equality checked below/native.
    extra = ('This document contains '+a+' '+b+' '+c+' '+d+'.' for a,b,c,d in itertools.product(
        ('some','several','a few'), ('short','ordinary','clearly separated'),
        ('sentences','descriptive paragraphs'), ('on the page','under a heading','within the same printed section')))
    expanded = (base+' '+clause for base in ('The document contains ordinary descriptive material.',
                'The printed document contains several short descriptive passages.') for clause in
                ('A heading is visible.', 'A short heading is visible.', 'One heading is clearly visible.',
                 'Several headings are visible.', 'A title appears above the passage.', 'Some paragraphs are separated by headings.'))
    gap = ['The printed document contains several short descriptive passages. Some paragraphs are separated by descriptive headings.']
    for text in itertools.chain(extra, expanded, gap, neutral_candidates()):
        n = len(tok.encode(text, add_special_tokens=False).ids)
        control_by_length.setdefault(n, text)
        if len(control_by_length) > 180: break
    groups = {'A_C0': [], 'B_FACTORIAL': []}
    for c in cases:
        conditions = ['C0'] if c['pool'] == 'calibration' else [*CELLS, 'N_style', 'N_history']
        controls = {}
        for con, active in [('N_style','C1'),('N_history','C3')] if c['pool'] == 'factorial' else []:
            wanted = len(tok.encode(render(content(c, active)), add_special_tokens=True).ids)
            active_text = c['style_intervention' if active=='C1' else 'history_intervention']
            body_count = len(tok.encode(active_text,add_special_tokens=False).ids)
            for n,candidate in control_by_length.items():
                if abs(n-body_count)>2: continue
                if len(tok.encode(render(content(c,con,candidate)),add_special_tokens=True).ids) == wanted:
                    controls[con] = candidate
                    break
            s.require(con in controls, f'No exact diagnostic match: {c["case_id"]} {con} {body_count} {wanted}; lengths {sorted(control_by_length)}')
        c['diagnostic_controls'] = controls
        for con in conditions:
            text = content(c, con, controls.get(con)); prompt = render(text)
            row = {'request_id': c['case_id']+'_'+con, 'case_id': c['case_id'], 'speaker_id': c['speaker_id'],
                'condition': con, 'factors': CELLS.get(con), 'family': c['family'], 'split': c['split'],
                'seed': 42, 'temperature': 0.0, 'top_p': 1.0, 'max_new_tokens': 96, 'stop': [],
                'cache_prompt': False, 'ignore_eos': False, 'parse_special': True,
                'messages': [{'role':'user','content':text}], 'prompt': prompt, 'prompt_sha256': s.th(prompt),
                'reference': c['reference'], 'reference_sha256': s.th(json.dumps(c['reference'],sort_keys=True)),
                'evidence_sha256': s.th(c['trusted_evidence']), 'question_sha256': s.th(c['question']),
                'context_sha256': s.th(c['fixed_context']), 'evaluation_date': c['evaluation_date'], 'applicability': c['applicability']}
            groups['A_C0' if c['pool']=='calibration' else 'B_FACTORIAL'].append(row)
    s.save(OUT/'materials_v1.json', {'cases': cases, 'provenance': 'AI-authored development materials, not independently validated', 'human_ratings': 0})
    s.save(OUT/'measurement_policy_v1.json', policy())
    s.save(OUT/'stimulus_validation_v1.json', validation)
    prior = []
    for p in Path('results').rglob('manifest.json'):
        d = s.load(p)
        if d.get('authorization',{}).get('authorization_id') == AUTH_ID: prior.append(p.as_posix())
    s.require(not prior, 'Prior scope execution must be reconciled')
    s.save(OUT/'authorization_v1.json', {'authorization_id': AUTH_ID, 'researcher': 'Yaxin ZHENG',
        'source': 'Explicit user message: Accelerated P1 Measurement Pilot and Focused Scientific Validation, sections 4-5',
        'human_decision_timestamp': None, 'registration_utc': s.b.utc_now(), 'maximum_new_attempts': 160,
        'category_caps': CAPS, 'unused_allocation_transfer': False, 'replaces_unexecuted_160_proposals': True,
        'no_retries': True, 'prior_scope_runs': prior, 'semantic_adoption': False,
        'allowed_phase': 'P1_ONLY', 'independent_validation_authorized': False, 'training_authorized': False})
    # Verify the immediately preceding sealed milestone; do not re-run historical suites.
    sealpath = Path('docs/validation/p5/oracle_diagnostic_v1/reproducibility_manifest_v1.json')
    seal = s.load(sealpath)
    for p,h in seal['artifact_sha256'].items(): s.require(s.sha256(Path(p)) == h, 'Historical seal changed: '+p)
    s.save(OUT/'preservation_baseline_v1.json', {'previous_seal': sealpath.as_posix(), 'sha256': s.sha256(sealpath),
        'verified_artifacts': len(seal['artifact_sha256']), 'log_sha256': s.sha256(Path('docs/research_development_log.md')),
        'git_head': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'git_status': subprocess.check_output(['git','status','--short'],text=True)})
    exe = Path(parent['model']['backend_file']).with_name('llama-tokenize.exe')
    native = s.load(s.b.FROZEN)['native_tokenizer_identity']
    s.require(s.sha256(exe) == native['tokenizer_sha256'], 'Tokenizer changed')
    for category, rows in groups.items():
        random.Random(731401 if category=='A_C0' else 731402).shuffle(rows)
        logs = []
        for order,r in enumerate(rows):
            argv = [str(exe.resolve()), '-m', str(Path(parent['model']['model_file']).resolve()), '--stdin', '--ids', '--offline']
            proc = subprocess.run(argv,input=r['prompt'].encode(),capture_output=True,timeout=60,
                env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            log = {'argv': argv,'prompt':r['prompt'],'returncode':proc.returncode,'stdout':proc.stdout.decode('utf-8','replace'),
                   'stderr':proc.stderr.decode('utf-8','replace'),'recorded_utc':s.b.utc_now(),'generation_requests':0}
            lp = OUT/'native_tokenizer'/category/f'{order:03d}.json'; s.save(lp,log)
            s.require(proc.returncode == 0, 'Native tokenizer failed')
            ids = ast.literal_eval(log['stdout'].strip())
            s.require(ids == tok.encode(r['prompt'],add_special_tokens=True).ids, 'Native/official tokenizer mismatch')
            s.require(tok.decode(ids,skip_special_tokens=False) == r['prompt'], 'Prompt reconstruction mismatch')
            r.update(order=order,input_token_ids=ids,input_tokens=len(ids),input_token_ids_sha256=s.th(str(ids)),context_remaining=4096-96-len(ids))
            s.require(r['context_remaining'] > 0, 'Context overflow')
            r['request_sha256'] = s.th(json.dumps(r,sort_keys=True,separators=(',',':')))
            logs.append({'path':lp.as_posix(),'sha256':s.sha256(lp)})
        plan = {k:parent[k] for k in ('model','template_path','template_sha256','candidate_metadata_sha256','decoding_policy')}
        plan.update(version='p1_measurement_manifest_v1',phase='P1',category=category,authorization_id=AUTH_ID,
            status='DEVELOPMENT_FROZEN_INPUTS_EXECUTION_SUBJECT_TO_PREFLIGHT',requests=rows,proposed_requests=len(rows),
            materials_sha256=s.sha256(OUT/'materials_v1.json'),policy_sha256=s.sha256(OUT/'measurement_policy_v1.json'),
            authorization_sha256=s.sha256(OUT/'authorization_v1.json'),native_tokenizer_logs=logs,
            native_tokenizer_identity=native,time_limit_minutes=60,no_retries=True,independent_validation=False)
        path = OUT/(category+'_manifest_v1.json');s.save(path,plan)
        print(json.dumps({'category':category,'requests':len(rows),'manifest_sha256':s.sha256(path),
              'actual_input_range':[min(r['input_tokens'] for r in rows),max(r['input_tokens'] for r in rows)]}),flush=True)
    s.save(OUT/'manifest_bindings_v1.json', {k:s.sha256(OUT/(k+'_manifest_v1.json')) for k in groups})


if __name__ == '__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    prepare()

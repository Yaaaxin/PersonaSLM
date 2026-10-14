"""Offline extraction baselines on saved development text, never generation."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import re
import statistics
import time
import tracemalloc

import p1c_semantic_review as a
import p1c_semantic_integrity as audit
from personaslm.response_status import classify_response, PREFIX, ROLE

OUT=a.ROOT/'boundary_baselines_v1'
METHODS=('frozen_v1','native_eos_only','literal_role_stop_shadow','role_or_section','fence_aware_role_or_section')
SECTION=re.compile(r'(?m)^(?:USER QUESTION|RECENT CONVERSATION):[ \t]*(?:\r?\n|$)')


def extract(raw,native,method):
    """Return original byte-preserving character spans; no evidence or score input."""
    if method not in METHODS:raise ValueError('Unknown method')
    if method=='frozen_v1':
        p=classify_response(raw,native,declared_stops=())
        return (p['first_span']['start'],p['first_span']['end']) if p['unit_identifiable'] else None
    eos=native.get('stop_type') in ('eos','eog') or native.get('stopped_eos') is True
    if method=='native_eos_only':return (0,len(raw)) if eos else None
    prefix=PREFIX.match(raw);start=prefix.end() if prefix else 0
    if method=='literal_role_stop_shadow':
        hits=[raw.index(m,start) for m in ('\nUser:','\nAssistant:') if m in raw[start:]]
    elif method=='role_or_section':
        hits=[m.start() for p in (ROLE,SECTION) for m in p.finditer(raw,start)]
    else:
        hits=[];offset=0;fence=None
        for line in raw.splitlines(keepends=True):
            stripped=line.lstrip();delimiter='```' if stripped.startswith('```') else '~~~' if stripped.startswith('~~~') else None
            if delimiter:
                if fence is None:fence=delimiter
                elif fence==delimiter:fence=None
            elif fence is None and offset>=start and (ROLE.match(line) or SECTION.match(line)):
                hits.append(offset)
            offset+=len(line)
    end=min(hits) if hits else len(raw) if eos else None
    return (start,end) if end is not None and raw[start:end].strip() else None


def fixture_bank():
    # Authored software diagnostic examples, not model generations or independent labels.
    examples=[
        ('role_transition','Answer.\nUser: Next?','Answer.'),
        ('assistant_replay','Answer.\nAssistant: Another answer.','Answer.'),
        ('question_heading','Answer.\n\nUSER QUESTION:\nNext?','Answer.'),
        ('context_heading','Answer.\n\nRECENT CONVERSATION:\nUser: Next?','Answer.'),
        ('fenced_role','Example:\n```text\nUser: literal label\n```\nDone.','Example:\n```text\nUser: literal label\n```\nDone.'),
        ('fenced_heading','Example:\n```text\nUSER QUESTION:\nliteral\n```\nDone.','Example:\n```text\nUSER QUESTION:\nliteral\n```\nDone.'),
        ('tilde_heading','Example:\n~~~\nRECENT CONVERSATION:\nliteral\n~~~\nDone.','Example:\n~~~\nRECENT CONVERSATION:\nliteral\n~~~\nDone.'),
        ('multiline_quote','The quotation is:\n"\nUSER QUESTION:\nliteral\n"\nDone.','The quotation is:\n"\nUSER QUESTION:\nliteral\n"\nDone.'),
        ('document_heading','The requested document follows.\nUSER QUESTION:\nA heading within the requested document.','The requested document follows.\nUSER QUESTION:\nA heading within the requested document.'),
        ('plain_eos','A complete answer.','A complete answer.'),
        ('inline_role','The literal User: string is part of my explanation.','The literal User: string is part of my explanation.'),
        ('fence_then_transition','Example:\n```\nUser: literal\n```\nDone.\nUser: Next?','Example:\n```\nUser: literal\n```\nDone.'),
    ]
    return [{'fixture_id':name,'raw':raw,'native':{'stop_type':'eos'},'authored_reference_content':expected,
             'provenance':'AI-authored diagnostic fixture; no human confirmation, independent evaluation or generation.'} for name,raw,expected in examples]


def run():
    a.require(not OUT.exists(),'Preserve previous baseline runs')
    structural=a.rows(a.ROOT/'measurement_v1/structural_review_view_v1.csv')
    primary={r['anonymous_response_id']:r for r in a.read(audit.PRIMARY)}
    secondary={r['anonymous_response_id']:r for r in a.read(audit.SECONDARY)}
    results=[];timing={};summaries={}
    for method in METHODS:
        current=[]
        for s in structural:
            rid=s['anonymous_response_id'];raw=s['raw_full_continuation'];native=json.loads(s['native_termination'])
            a.require(a.text_sha(raw)==s['raw_text_sha256'],'Raw text changed')
            span=extract(raw,native,method);view=raw[span[0]:span[1]] if span else None
            p=primary[rid];q=secondary[rid];match=None
            if view is not None and rid not in audit.BOUNDARY and view.strip()==p['raw_first_reply'].strip():match='PRIMARY_CONTENT'
            elif view is not None and rid in audit.BOUNDARY and view.strip()==q['secondary_evaluation_view'].strip():match='PROPOSED_SECONDARY_CONTENT'
            rating=(p if match=='PRIMARY_CONTENT' else q)['reviewed_AI_ratings'] if match else None
            current.append({'anonymous_response_id':rid,'method':method,'raw_sha256':s['raw_text_sha256'],
                'frozen_structural_status':s['frozen_structural_status'],'native_termination':native,
                'candidate_start':span[0] if span else None,'candidate_end':span[1] if span else None,
                'candidate_text':view,'candidate_sha256':a.text_sha(view) if view is not None else None,
                'existing_proposal_content_match':match,'provisional_existing_ratings':rating,
                'independent_boundary_ground_truth':None,'boundary_accuracy':None,
                'scope':'Whitespace-only content equivalence transfers an existing unconfirmed proposal; unmatched candidates are not scored. No official semantic effects.'})
        results.extend(current)
        summaries[method]={'returned_candidate':sum(r['candidate_text'] is not None for r in current),
            'reference_matches':dict(Counter(str(r['existing_proposal_content_match']) for r in current)),
            'provisional_factual':dict(Counter(r['provisional_existing_ratings']['factual_consistency'] for r in current if r['provisional_existing_ratings'])),
            'provisional_temporal':dict(Counter(r['provisional_existing_ratings']['temporal_consistency'] for r in current if r['provisional_existing_ratings'])),
            'provisional_task':dict(Counter(str(r['provisional_existing_ratings']['task_success']) for r in current if r['provisional_existing_ratings'])),
            'independent_boundary_accuracy':None}
        cpu=[];wall=[]
        for repeat in range(5):
            c=time.process_time_ns();w=time.perf_counter_ns()
            for _ in range(50):
                for s in structural:extract(s['raw_full_continuation'],json.loads(s['native_termination']),method)
            cpu.append((time.process_time_ns()-c)/(50*72));wall.append((time.perf_counter_ns()-w)/(50*72))
        tracemalloc.start()
        for s in structural:extract(s['raw_full_continuation'],json.loads(s['native_termination']),method)
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        timing[method]={'median_cpu_ns_per_record':statistics.median(cpu),'median_wall_ns_per_record':statistics.median(wall),
            'cpu_batch_ns_per_record':cpu,'wall_batch_ns_per_record':wall,'one_pass_traced_python_peak_bytes':peak,
            'scope':'Includes native JSON decoding; files preloaded. Tracemalloc is not process peak RAM. Python-only extraction, not model runtime.'}
    fixtures=fixture_bank();fixture_results=[]
    for f in fixtures:
        for method in METHODS:
            span=extract(f['raw'],f['native'],method);view=f['raw'][span[0]:span[1]] if span else None
            fixture_results.append({'fixture_id':f['fixture_id'],'method':method,'candidate':view,
                'matches_authored_reference':view is not None and view.strip()==f['authored_reference_content'].strip(),
                'abstained':view is None,'false_split':view is not None and len(view.strip())<len(f['authored_reference_content'].strip()),
                'scope':'Diagnostic fixture result only, not independent empirical accuracy.'})
    a.write(OUT/'saved_output_baseline_rows_v1.json',results);a.write_csv(OUT/'saved_output_baseline_rows_v1.csv',results)
    a.write(OUT/'authored_diagnostic_fixtures_v1.json',fixtures);a.write_csv(OUT/'fixture_results_v1.csv',fixture_results)
    a.write(OUT/'summary_v1.json',{'version':'p1c_offline_boundary_baselines_v1','saved_generations':72,'new_generations':0,
        'methods':summaries,'timing':timing,'python':platform.python_version(),'platform':platform.platform(),
        'fixture_summary':{m:{'matching_content':sum(r['matches_authored_reference'] for r in fixture_results if r['method']==m),
            'false_splits':sum(r['false_split'] for r in fixture_results if r['method']==m),
            'abstentions':sum(r['abstained'] for r in fixture_results if r['method']==m),'denominator':len(fixtures)} for m in METHODS},
        'limitations':'Development reference agreement is circular, not independently annotated accuracy. Literal stop shadows are post-hoc truncation, not regenerated stop-sequence counterfactuals. Official template/constrained decoding require future generation and are not run.',
        'semantic_effect_analysis':False,'human_ratings_created':False})
    a.write(OUT/'manifest_v1.json',{'software_recorded_utc':datetime.now(timezone.utc).isoformat(),
        'code_sha256':a.sha(__file__),'source_sha256':{str(p):a.sha(p) for p in (a.ROOT/'measurement_v1/structural_review_view_v1.csv',audit.PRIMARY,audit.SECONDARY)},
        'frozen_parser_sha256':a.sha('src/personaslm/response_status.py'),'files':{p.name:a.sha(p) for p in OUT.iterdir()},
        'new_inference':0,'official_semantic_effects':0,'new_original_algorithm_claim':False})
    print(json.dumps({'methods':summaries,'fixture_summary':a.read(OUT/'summary_v1.json')['fixture_summary'],'new_inference':0},indent=2))


if __name__=='__main__':run()

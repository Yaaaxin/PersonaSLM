"""Offline continuation/heading diagnostics; no primary boundary replacement."""
from collections import Counter,defaultdict
import json
import re
import statistics
import time
from pathlib import Path
import p1d_budget_calibration as b
from p1d_budget_measurement import OUT as MEASURE
from p1d_design import csvwrite
from p1c_boundary_baselines import extract,METHODS
from p1d_boundary_locality import inspect

OUT=b.OUT/'boundary_diagnostics_v1'
HEADING=re.compile(r'(?m)^(?:CURRENT QUESTION|USER RESPONSE)[ \t]*:?[ \t]*(?:\r?\n|$)')

def heading_shadow(raw,native):
    """Post-hoc heading heuristic, can falsely split requested/quoted documents."""
    base=extract(raw,native,'literal_role_stop_shadow')
    start=base[0] if base else 0;end=base[1] if base else len(raw)
    hits=[m.start() for m in HEADING.finditer(raw,start) if m.start()<end]
    if not hits:return base
    end=min(hits)
    return (start,end) if raw[start:end].strip() else None

def run():
    audit=b.load(MEASURE/'execution_integrity_v1.json');assert audit['results']==144
    cases={c['case_id']:c for c in b.load(b.DEV/'development_examples_v5.json')['cases']}
    rows=[];candidates=[];lines=Counter();items=[]
    for item in audit['rows']:
        q=item['request'];r=item['result'];raw=r['raw_response'];first=r['response_status']['first_span']['text'];c=cases[q['case_id']]
        refs=q['reference'];promise=c['fixed_context'].split('Assistant:',1)[1].strip()
        complete_lines=raw.splitlines();lines.update(complete_lines[:-1]) # final cap fragment is not presumed complete
        values=lambda text:[x['key'] for x in refs if x['value'].lower() in text.lower()]
        row={'request_id':q['request_id'],'case_id':q['case_id'],'budget':q['max_new_tokens'],'condition':q['condition'],
            'original_status':r['response_status']['status'],'raw_sha256':r['raw_text_sha256'],'first_sha256':b.th(first),
            'raw_required_literal_mentions':values(raw),'primary_required_literal_mentions':values(first),
            'original_context_promise_occurrences':raw.count(promise),'primary_equals_context_promise':first.strip()==promise,
            'question_echo_count':raw.count(c['question']),'anchored_Assistant_markers':len(re.findall(r'(?m)^Assistant:',raw)),
            'current_question_headers':len(re.findall(r'(?m)^CURRENT QUESTION',raw)),
            'user_response_headers':len(re.findall(r'(?m)^USER RESPONSE',raw)),
            'last_line':complete_lines[-1] if complete_lines else '',
            'primary_preserved':True,'literal_match_is_semantic_score':False}
        rows.append(row);items.append((raw,r['raw_termination']))
        for method in (*METHODS,'prefix_locality_diagnostic','question_response_heading_shadow'):
            if method=='prefix_locality_diagnostic':
                p=inspect(raw,r['raw_termination'])['local_prefix_candidate'];span=(p['start'],p['end']) if p else None
            elif method=='question_response_heading_shadow':span=heading_shadow(raw,r['raw_termination'])
            else:span=extract(raw,r['raw_termination'],method)
            text=raw[span[0]:span[1]] if span else None
            candidates.append({'request_id':q['request_id'],'budget':q['max_new_tokens'],'method':method,'start':span[0] if span else None,
                'end':span[1] if span else None,'candidate_text':text,'candidate_sha256':b.th(text) if text is not None else None,
                'equal_primary_text':text==first,'required_literal_mentions':values(text) if text else [],
                'independent_boundary_accuracy':None,'semantic_adoption':None})
    times={}
    for method in (*METHODS,'prefix_locality_diagnostic','question_response_heading_shadow'):
        fun=inspect if method=='prefix_locality_diagnostic' else heading_shadow if method=='question_response_heading_shadow' else lambda x,n:extract(x,n,method)
        batches=[]
        for _ in range(5):
            cpu=time.process_time_ns();wall=time.perf_counter_ns()
            for _ in range(20):
                for raw,native in items:fun(raw,native)
            batches.append({'cpu_ns_per_output':(time.process_time_ns()-cpu)/(20*144),'wall_ns_per_output':(time.perf_counter_ns()-wall)/(20*144)})
        times[method]={'batches':batches,'median_cpu_ns_per_output':statistics.median(x['cpu_ns_per_output'] for x in batches)}
    summary={'version':'p1d_saved_continuation_diagnostics_v1','records':144,'new_generations':0,'changed_primary_labels':0,
        'by_budget':{cap:{'n':48,'raw_with_required_literal':sum(bool(r['raw_required_literal_mentions']) for r in rows if r['budget']==cap),
            'primary_with_required_literal':sum(bool(r['primary_required_literal_mentions']) for r in rows if r['budget']==cap),
            'exact_context_promise_only':sum(r['primary_equals_context_promise'] for r in rows if r['budget']==cap),
            'question_echo_outputs':sum(r['question_echo_count']>0 for r in rows if r['budget']==cap)} for cap in (96,192,256)},
        'methods':{m:{'candidates':sum(r['candidate_text'] is not None for r in candidates if r['method']==m),
            'changed_text_from_primary':sum(r['candidate_text'] is not None and not r['equal_primary_text'] for r in candidates if r['method']==m),
            'with_required_literal':sum(bool(r['required_literal_mentions']) for r in candidates if r['method']==m)} for m in times},
        'timings':times,'timing_scope':'Offline Python methods, preloaded strings; no model execution or I/O; process CPU and wall reported',
        'limits':'Reference literal absence is a lexical diagnostic, not proof against paraphrases. Candidate agreement is not boundary accuracy. Heading shadow is post-hoc and can split legitimate document content. Stops/templates require future authorized generation.',
        'source_sha256':{str(p):b.sha256(p) for p in (MEASURE/'execution_integrity_v1.json',Path(__file__),Path('src/personaslm/response_status.py'))}}
    OUT.mkdir(parents=True,exist_ok=True);csvwrite(OUT/'raw_continuation_diagnostics_v1.csv',rows);csvwrite(OUT/'boundary_candidate_views_v1.csv',candidates)
    b.save(OUT/'complete_line_inventory_v1.json',[{'line':line,'occurrences':n} for line,n in lines.most_common()])
    b.save(OUT/'summary_v1.json',summary);print(json.dumps({k:v for k,v in summary.items() if k in ('by_budget','methods')},indent=2))

if __name__=='__main__':run()

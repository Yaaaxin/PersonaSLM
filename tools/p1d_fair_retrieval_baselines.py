"""Equal-cardinality, tie-aware retrieval diagnostics on registered development data.

No generation, independent-test input, learned parameter or novelty claim.
BM25 is a transparent mathematical adaptation, not a Lucene reproduction.
"""
from collections import Counter
import json
import math
from pathlib import Path
import re
import statistics
import time
import p1d_budget_calibration as b
from p1d_design import csvwrite

OUT=b.OUT/'offline_retrieval_v1'
METHODS=('random_top1','binary_overlap_top1','bm25_top1','time_then_bm25_top1','entity_time_then_bm25_top1')

def words(text):
    return re.findall(r'\w+',text.lower())

def bm25(texts,query,k1=1.2,length_weight=.75):
    if not texts:return []
    counts=[Counter(words(t)) for t in texts];lengths=[sum(c.values()) for c in counts]
    avg=statistics.mean(lengths) or 1.;terms=set(words(query));n=len(texts)
    idf={t:math.log(1+(n-sum(t in c for c in counts)+.5)/(sum(t in c for c in counts)+.5)) for t in terms}
    return [sum(idf[t]*(c[t]*(k1+1))/(c[t]+k1*(1-length_weight+length_weight*length/avg)) for t in terms if c[t]) for c,length in zip(counts,lengths)]

def ranking(pool,query,method):
    """Return all top ties; exactly one item is retained under uniform tie breaking."""
    if method not in METHODS:raise ValueError(method)
    indices=list(range(len(pool)))
    if method.startswith('entity_time'):
        indices=[i for i,x in enumerate(pool) if x['entity']==query['entity'] and x['start']<=query['date']<=x['end']]
    elif method.startswith('time_'):
        indices=[i for i,x in enumerate(pool) if x['start']<=query['date']<=x['end']]
    # Empty constrained retrieval is explicit abstention, never a silent fallback.
    if not indices:return []
    if method=='random_top1':scores=[0. for _ in indices]
    elif method=='binary_overlap_top1':
        terms=set(words(query['text']));scores=[len(terms & set(words(pool[i]['text']))) for i in indices]
    else:scores=bm25([pool[i]['text'] for i in indices],query['text'])
    peak=max(scores)
    return [indices[j] for j,s in enumerate(scores) if math.isclose(s,peak,rel_tol=1e-12,abs_tol=1e-12)]

def evaluate(cases):
    rows=[]
    for c in cases:
        pool=[{**next(f for f in c['facts'] if f['id']==h['source_id']),'text':h['text']} for h in c['histories'].values() if h['source_id']]
        assert len(pool)==4 and len({p['id'] for p in pool})==4
        q={'text':c['question']+' '+c['fixed_context'],'entity':c['target_entity'],'date':c['query_date']}
        correct=[i for i,x in enumerate(pool) if x['entity']==q['entity'] and x['start']<=q['date']<=x['end']]
        assert len(correct)==1
        for method in METHODS:
            ties=ranking(pool,q,method)
            probability=sum(i in correct for i in ties)/len(ties) if ties else 0.
            rows.append({'case_id':c['case_id'],'method':method,'candidate_pool':4,'retained_items':int(bool(ties)),
                'top_tie_ids':'|'.join(pool[i]['id'] for i in ties),'tie_count':len(ties),
                'target_query_valid_selection_probability':probability,
                'uses_provided_structured_date':method.startswith(('time_','entity_time')),
                'uses_provided_structured_entity':method.startswith('entity_time'),
                'generated_answer_quality':None,'persona_fidelity':None})
    return rows

def run():
    source=b.DEV/'development_examples_v5.json';cases=b.load(source)['cases'];assert len(cases)==16
    rows=evaluate(cases);batches=[]
    for _ in range(5):
        wall=time.perf_counter_ns();cpu=time.process_time_ns()
        for _ in range(50):evaluate(cases)
        batches.append({'cpu_ns_per_case_method':(time.process_time_ns()-cpu)/(50*len(rows)),
            'wall_ns_per_case_method':(time.perf_counter_ns()-wall)/(50*len(rows))})
    summary={'version':'fair_development_retrieval_v1','development_cases':16,'generation_calls':0,
        'source_sha256':b.sha256(source),'script_sha256':b.sha256(Path(__file__)),
        'bm25':{'k1':1.2,'b':.75,'idf':'log(1 + (N - df + 0.5)/(df + 0.5))','query_terms':'unique lowercase regex word tokens',
            'reference':'https://lucene.apache.org/core/9_12_1/core/org/apache/lucene/search/similarities/BM25Similarity.html'},
        'methods':{m:{'expected_target_query_valid_top1':sum(r['target_query_valid_selection_probability'] for r in rows if r['method']==m),
            'cases':16,'tied_cases':sum(r['tie_count']>1 for r in rows if r['method']==m)} for m in METHODS},
        'tie_policy':'Exact expected top-1 retention under uniform tie breaking; no arbitrary source-ID advantage',
        'cpu_cost_batches':batches,'cost_scope':'Pure Python retrieval including pool preparation, no model or I/O; concurrent CPU calibration can affect wall time',
        'classification':'EXISTING_METHOD_ENGINEERING_ADAPTATION',
        'limitations':['Four curated ledger candidates, no natural-memory or independent test evaluation',
            'Date/entity supplied by author metadata; extraction errors are not evaluated',
            'Time-filtered and entity-filtered methods have privileged structured input, so comparisons are diagnostics, not equal-information superiority',
            'A selected locker fact does not itself answer a multi-component/relational question',
            'LongMemEval timestamp pruning reorders candidates using an LLM-derived interval; this hard interval filter is not its replication',
            'No measured factual, task-delivery or Persona Fidelity gain']}
    OUT.mkdir(parents=True,exist_ok=True);csvwrite(OUT/'selection_records_v1.csv',rows);b.save(OUT/'summary_v1.json',summary)
    print(json.dumps(summary['methods'],indent=2))

if __name__=='__main__':run()

"""Retrospective literal-component baseline on frozen P1b outputs; no inference."""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import time

import p1c_design as d
import p1c_decisions as p

SOURCE=Path('docs/validation/p1b/confirmed_analysis_v1/analysis_v1/unblinded_analysis_dataset_v1.json')
SOURCE_MANIFEST=SOURCE.parent/'analysis_reproducibility_manifest_v1.json'
POLICY={'version':'literal_component_presence_baseline_v1','status':'RETROSPECTIVE_DEVELOPMENT_DIAGNOSTIC',
        'rule':'All reference component values must appear as contiguous case-insensitive Unicode word-token sequences in the frozen first reply.',
        'inputs':'Reference components are oracle evaluation metadata, not a deployment-time verifier.',
        'comparators':['always_predict_full','never_predict_full','literal_component_presence'],
        'human_reference':'Researcher-confirmed AI-assisted answer_delivery == FULL_ANSWER',
        'selection':'All 192 existing P1b outputs; no condition/correctness filtering; no tuning or regeneration.',
        'limitations':'Mention is not assertion, support, temporal validity or answer delivery. Reference leakage makes this an oracle-aided baseline, not a new algorithm.',
        'new_generations':0}


def contains_phrase(text, phrase):
    tokens=re.findall(r'\w+',text.casefold());need=re.findall(r'\w+',str(phrase).casefold())
    if not need:raise ValueError('Empty component')
    return any(tokens[i:i+len(need)]==need for i in range(len(tokens)-len(need)+1))


def evaluate(rows):
    results=[]
    for row in rows:
        d.require(d.text_hash(row['raw_first_reply'])==row['first_reply_sha256'],'First-reply hash differs')
        components=json.loads(row['reference_answer_json'])['components']
        d.require(bool(components),'Missing components')
        present={k:contains_phrase(row['raw_first_reply'],v) for k,v in components.items()}
        results.append({'response_id':row['anonymous_response_id'],'case_id':row['case_id'],'speaker_id':row['persona_id'],
            'family':row['family'],'literal_components_present':present,'literal_all_present':all(present.values()),
            'confirmed_full_answer':row['confirmed_answer_delivery']=='FULL_ANSWER',
            'original_delivery':row['confirmed_answer_delivery'],'original_factual_label':row['confirmed_factual_consistency'],
            'original_semantic_completeness':row['confirmed_semantic_completeness'],
            'first_reply_sha256':row['first_reply_sha256'],'source_row_sha256':d.canonical(row)})
    tables={}
    for name in POLICY['comparators']:
        table=Counter()
        for row in results:
            pred=True if name=='always_predict_full' else False if name=='never_predict_full' else row['literal_all_present']
            table['TP' if pred and row['confirmed_full_answer'] else 'FP' if pred else 'FN' if row['confirmed_full_answer'] else 'TN']+=1
        tables[name]={k:table[k] for k in ('TP','FP','FN','TN')}
    return results,tables


def run(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve earlier baseline attempts')
    m=p.decision_json(SOURCE_MANIFEST)
    d.require(d.sha(SOURCE)==m['files'][SOURCE.name],'Frozen analysis source hash differs')
    rows=p.decision_json(SOURCE)['rows']
    d.require(len(rows)==len({r['anonymous_response_id'] for r in rows})==192,'Expected 192 unique outputs')
    d.require(len({r['case_id'] for r in rows})==24 and len({r['persona_id'] for r in rows})==12,'Unit mismatch')
    d.write_json(output/'baseline_policy_v1.json',POLICY)
    start=time.perf_counter();table,counts=evaluate(rows);elapsed=time.perf_counter()-start
    table2,counts2=evaluate(rows);d.require(table==table2 and counts==counts2,'Replay mismatch')
    d.write_csv(output/'case_response_diagnostics_v1.csv',table)
    summary={'version':POLICY['version'],'records':192,'paired_cases':24,'speaker_clusters':12,'comparison_tables':counts,
             'false_positive_delivery_categories':dict(Counter(r['original_delivery'] for r in table if r['literal_all_present'] and not r['confirmed_full_answer'])),
             'families':{f:{'records':sum(r['family']==f for r in table),'false_positive':sum(r['family']==f and r['literal_all_present'] and not r['confirmed_full_answer'] for r in table),
                            'false_negative':sum(r['family']==f and not r['literal_all_present'] and r['confirmed_full_answer'] for r in table)} for f in sorted({r['family'] for r in table})},
             'repeat_numerical_agreement':True,'new_generations':0,'originality':'KNOWN_ENGINEERING_BASELINE',
             'scientific_level':'LEVEL_0_ENGINEERING_DIAGNOSTIC','fidelity':'NOT_EVALUATED; no outputs modified'}
    d.write_json(output/'baseline_results_v1.json',summary)
    d.write_json(output/'reproducibility_v1.json',{'executed_utc':d.now(),'source':str(SOURCE),'source_sha256':d.sha(SOURCE),
         'original_manifest_sha256':d.sha(SOURCE_MANIFEST),'code_sha256':d.sha(Path(__file__)),
         'policy_sha256':d.sha(output/'baseline_policy_v1.json'),'result_sha256':d.sha(output/'baseline_results_v1.json'),
         'evaluation_wall_seconds':elapsed,'peak_RAM':'not measured','new_generations':0,'new_human_decisions':0})
    return summary


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True)
    print(json.dumps(run(a.parse_args().output),indent=2))

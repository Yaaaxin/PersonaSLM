"""Gated paired boundary/structural diagnostics reusing the registered statistics."""
import argparse
import json
from collections import Counter
from pathlib import Path

import p1c_semantic_review as a
import p1c_semantic_analysis as s
import p1c_integrity_registration as gate


def diagnostics(primary,secondary,spec,structural,replicates=10000):
    """Pure function. Real annotations are loaded only after CLI confirmation checks."""
    index={r['anonymous_response_id']:r for r in primary}
    a.require(len(index)==len(primary),'Duplicate primary ID')
    cross=[];structural_effects=[]
    for metric in a.FIELDS:
        counts=Counter((structural[r['anonymous_response_id']]['frozen_structural_status'],str(r['ratings'][metric])) for r in primary)
        cross.extend({'metric':metric,'structural_status':status,'semantic_value':value,'count':n} for (status,value),n in sorted(counts.items()))
    for metric in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS','first_reply_identifiable','native_eos','native_budget'):
        cases=[]
        for cid,speaker in sorted(spec['cases'].items()):
            cells=[r for r in primary if r['case_id']==cid]
            a.require(len(cells)==6 and {r['condition'] for r in cells}==set(spec['condition_order']),'Case cells differ')
            values={}
            for r in cells:
                src=structural[r['anonymous_response_id']]
                value=(src['frozen_structural_status']==metric if metric in ('COMPLETE','TRUNCATED','CROSS_TURN','AMBIGUOUS') else
                    src['unit_identifiable'] if metric=='first_reply_identifiable' else
                    src['native_stop'] in ('eos','eog') if metric=='native_eos' else src['native_stop']=='limit')
                values[r['condition']]=float(value)
            cases.append({'case_id':cid,'speaker_id':speaker,'values':values})
        for name,weights in spec['weights'].items():
            structural_effects.append({'metric':metric,'contrast':name,**s.stats.summarize(cases,weights,replicates=replicates)})
    deltas=[]
    if secondary is not None:
        other={r['anonymous_response_id']:r for r in secondary}
        a.require(set(other)==set(index),'Sensitivity IDs differ')
        for rid,r in index.items():
            a.require(all(r[k]==other[rid][k] for k in ('case_id','condition','persona_id')),'Sensitivity routing differs')
        metrics=s.scalar_metrics(primary[0]['ratings'])
        for metric,(_,lo,hi) in metrics.items():
            cases=[]
            for cid,speaker in sorted(spec['cases'].items()):
                values={}
                for r in primary:
                    if r['case_id']!=cid:continue
                    first=s.scalar_metrics(r['ratings'])[metric][0]
                    second=s.scalar_metrics(other[r['anonymous_response_id']]['ratings'])[metric][0]
                    values[r['condition']]=None if first is None or second is None else second-first
                cases.append({'case_id':cid,'speaker_id':speaker,'values':values})
            for name,weights in spec['weights'].items():
                value=s.stats.summarize(cases,weights,replicates=replicates,lower=lo-hi,upper=hi-lo)
                value['unknown_bound_cluster_sensitivity']=s.bound_sensitivity(value,replicates)
                deltas.append({'metric':metric,'contrast':name,**value,
                    'estimand':'Within-output secondary-minus-primary measurement difference, then original paired-case contrast. Unknown deltas stay unknown; no difference of differently selected assessed-only means.',
                    'limitation':'Unknown-delta bounds can be conservative; no factual recoding or new primary endpoint.'})
    return {'primary_structure_semantic_crosstabs':cross,'structural_effects':structural_effects,'paired_boundary_sensitivity_effect_changes':deltas,
        'scope':'Exploratory measurement robustness; same 16 weights, six clusters. No independent boundary accuracy or pure-mechanism claim.'}


def run(registration,analysis,output):
    registration=Path(registration);analysis=Path(analysis);output=Path(output)
    a.require(not output.exists(),'Cannot overwrite diagnostics')
    rm=a.read(registration/'registration_manifest_v1.json')
    for name,digest in rm['files'].items():a.require(a.sha(registration/name)==digest,'Registration changed')
    # Explicit confirmation remains mandatory before any real treatment data are loaded.
    expected=gate.confirmed(a.read(registration/'actual_researcher_decision_v1.json'))
    a.require(expected==a.read(registration/'confirmed_annotations_v1.json'),'Confirmed snapshot reconstruction differs')
    am=a.read(analysis/'analysis_manifest_v1.json')
    a.require(am['registration_sha256']==a.sha(registration/'registration_manifest_v1.json'),'Wrong analysis registration')
    for name,digest in am['files'].items():a.require(a.sha(analysis/name)==digest,'Analysis changed')
    views={name:a.read(analysis/(name+'_unblinded_dataset_v1.json')) for name in expected}
    for name,rows in views.items():
        a.require(len(rows)==72 and len({r['anonymous_response_id'] for r in rows})==72,'Analysis inventory differs')
        actual={r['anonymous_response_id']:r['ratings'] for r in rows}
        a.require(actual=={r['anonymous_response_id']:r['ratings'] for r in expected[name]},'Analysis ratings differ')
    struct={r['anonymous_response_id']:{'frozen_structural_status':r['frozen_structural_status'],
        'native_stop':json.loads(r['native_termination'])['stop_type'],
        'unit_identifiable':json.loads(r['parser_trace'])['unit_identifiable']} for r in a.rows(a.ROOT/'measurement_v1/structural_review_view_v1.csv')}
    spec=a.read(s.PREP/'analysis_specification_v1.json')
    value=diagnostics(views['primary'],views.get('secondary'),spec,struct)
    a.require(value==diagnostics(views['primary'],views.get('secondary'),spec,struct),'Reconstruction differs')
    a.write(output/'paired_measurement_diagnostics_v1.json',value)
    a.write(output/'manifest_v1.json',{'registration_sha256':a.sha(registration/'registration_manifest_v1.json'),
        'analysis_sha256':a.sha(analysis/'analysis_manifest_v1.json'),'code_sha256':a.sha(__file__),
        'files':{p.name:a.sha(p) for p in output.iterdir()},'reconstructed_twice':True,'new_generations':0})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('registration','analysis','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();run(args.registration,args.analysis,args.output)

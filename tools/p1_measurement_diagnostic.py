"""One P1 category-C output-instruction diagnostic on calibration cases only."""
import ast
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import p1_measurement_materials as m
s=m.s


def instruction(c,arm):
    concise='Give only the requested answer. Do not provide reasoning, explanations or citations. Include every requested answer component.'
    if arm=='concise':return concise
    s.require(arm=='date_slots','Unregistered diagnostic arm')
    slots={'single_lookup':'date | assigned bay','dual_component':'date | assigned bay | collection window',
           'relational_chain':'date | assigned bay | connected zone | departure gate',
           'dated_comparison':'date | assigned bay'}[c['family']]
    return concise+' Use this field order: '+slots+'. Write one line for each requested date. Select records whose validity interval contains that requested date, not another date.'


def diagnostic_content(c,arm):
    text=m.content(c,'C0')
    return text.replace('Trusted evidence:\n','Output instruction:\n'+instruction(c,arm)+'\nTrusted evidence:\n',1)


def prepare():
    cases=[c for c in s.load(m.OUT/'materials_v1.json')['cases'] if c['case_id'] in {f'p1_measure_calibration_{i:02d}' for i in range(8)}]
    parent=s.load(m.OUT/'A_C0_manifest_v1.json');old={r['case_id']:r for r in parent['requests']}
    dest=m.OUT/'C_DIAGNOSTIC';rows=[];logs=[]
    policy={'phase':'P1 measurement diagnosis ONLY','category':'C_DIAGNOSTIC','requests':16,
        'case_selection':'Calibration indices 00-07: first complete four-family block, two cases per family. No factorial cases or outputs; no selection for favorable S/F/H effects.',
        'arms':['concise','date_slots'],'principal_purpose':'Determine whether output instructions permit requested-date/component measurement; not Persona or pure formatting causal identification.',
        'changed':'Output instruction only; concise suppresses explanation, date_slots additionally specifies fields and requested-date selection. Package-level diagnostic.',
        'fixed':'All original trusted evidence, reference answers, question, evaluation date, speaker identity, C0 no S/F/H, model/template, seed42 and96token budget.',
        'comparison':'Exact original C0 outputs plus two new matched instructions. Development, not replication or significance testing.',
        'one_shot_selection':'Select an arm only if >=7/8 requested answer forms complete, zero unresolved response boundaries, and at least one correct complete answer per two-case task family. These are small-sample diagnostic criteria, not population guarantees or the 80-95% target.',
        'tie_break':'If both qualify choose concise (smaller intervention), irrespective of effect directions. No factorial treatment outputs available.',
        'otherwise':'Keep B_FACTORIAL NO_GO; retain the unexecuted preselected pilot and do not optimize/remove difficult cases. Use offline scoring/measurement work; no arbitrary further sweep.',
        'scoring':'Original rubric retained; independently proposed AI ratings plus preserved automatic v1 and corrected v2. No human adoption inferred.',
        'automatic_v2_sha256':s.sha256(Path('tools/p1_measurement_scoring_v2.py')),
        'before_outputs':True,'human_annotation_timestamp':None}
    s.save(dest/'prospective_policy_v1.json',policy)
    template=Path(parent['template_path']).read_text(encoding='utf-8')
    sys.path.insert(0,str(Path('results/p1d_final_preparation/v1/tokenizer_runtime').resolve()))
    from tokenizers import Tokenizer
    tok=Tokenizer.from_file('results/p1d_final_preparation/v1/official_tokenizer/tokenizer.json')
    for c in cases:
        for arm in policy['arms']:
            r={k:v for k,v in old[c['case_id']].items() if k not in ('order','request_sha256','input_token_ids','input_token_ids_sha256','input_tokens','context_remaining')}
            text=diagnostic_content(c,arm);prompt=s.render(template,[{'role':'user','content':text}])
            r.update(request_id=c['case_id']+'_diagnostic_'+arm,diagnostic_arm=arm,
                parent_request_id=old[c['case_id']]['request_id'],parent_request_sha256=old[c['case_id']]['request_sha256'],
                messages=[{'role':'user','content':text}],prompt=prompt,prompt_sha256=s.th(prompt))
            rows.append(r)
    random.Random(731621).shuffle(rows)
    exe=Path(parent['model']['backend_file']).with_name('llama-tokenize.exe')
    for order,r in enumerate(rows):
        argv=[str(exe.resolve()),'-m',str(Path(parent['model']['model_file']).resolve()),'--stdin','--ids','--offline']
        proc=subprocess.run(argv,input=r['prompt'].encode(),capture_output=True,timeout=60,
            env={k:v for k,v in os.environ.items() if not k.upper().startswith('LLAMA_ARG_')},creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        log={'argv':argv,'prompt':r['prompt'],'returncode':proc.returncode,'stdout':proc.stdout.decode('utf-8','replace'),
             'stderr':proc.stderr.decode('utf-8','replace'),'recorded_utc':s.b.utc_now(),'generation_requests':0}
        lp=dest/'native_tokenizer'/f'{order:03d}.json';s.save(lp,log)
        s.require(proc.returncode==0,'Native tokenizer failed');ids=ast.literal_eval(log['stdout'].strip())
        s.require(ids==tok.encode(r['prompt'],add_special_tokens=True).ids and tok.decode(ids,skip_special_tokens=False)==r['prompt'],'Token reconstruction')
        r.update(order=order,input_tokens=len(ids),input_token_ids=ids,input_token_ids_sha256=s.th(str(ids)),context_remaining=4096-96-len(ids))
        r['request_sha256']=s.th(json.dumps(r,sort_keys=True,separators=(',',':')))
        logs.append({'path':lp.as_posix(),'sha256':s.sha256(lp)})
    plan={k:v for k,v in parent.items() if k not in ('category','requests','proposed_requests','native_tokenizer_logs')}
    plan.update(category='C_DIAGNOSTIC',requests=rows,proposed_requests=16,native_tokenizer_logs=logs,
        diagnostic_policy_path=(dest/'prospective_policy_v1.json').as_posix(),diagnostic_policy_sha256=s.sha256(dest/'prospective_policy_v1.json'))
    path=m.OUT/'C_DIAGNOSTIC_manifest_v1.json';s.save(path,plan)
    s.save(m.OUT/'C_DIAGNOSTIC_binding_v1.json',{'C_DIAGNOSTIC':s.sha256(path)})
    print(json.dumps({'requests':16,'category':'C_DIAGNOSTIC','manifest_sha256':s.sha256(path)}))


if __name__=='__main__':prepare()

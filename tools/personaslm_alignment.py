"""Prospective S/F/H estimands and authored fidelity calibration materials.

Does not change adopted protocols, infer model effects, or create human ratings.
"""
from pathlib import Path
import json
import re
import p1d_budget_calibration as io
from p1d_design import csvwrite

OUT=Path('docs/validation/research_alignment_v1')
CELLS={'C0':(0,0,0),'C1':(1,0,0),'C2':(0,1,0),'C3':(0,0,1),
       'C4':(1,1,0),'C5':(1,0,1),'C6':(0,1,1),'C7':(1,1,1)}

def contrasts():
    result={}
    for label,indices in [('S',(0,)),('F',(1,)),('H',(2,)),('SxF',(0,1)),('SxH',(0,2)),('FxH',(1,2)),('SxFxH',(0,1,2))]:
        weights={}
        for c,x in CELLS.items():
            sign=1
            for i in indices:sign*=2*x[i]-1
            weights[c]=sign/(2**(3-len(indices)))
        result[label]={'weights':weights,'estimand':'average factorial contrast over remaining factors'}
    result['H1_SxH_at_F0']={'weights':dict(zip(CELLS,[1,-1,0,-1,0,1,0,0])),
                          'estimand':'[Y(C5)-Y(C3)]-[Y(C1)-Y(C0)]; no F=1 averaging'}
    for name,a,b in [('style_F0H0','C1','C0'),('history_S0F0','C3','C0'),
                     ('style_vs_diagnostic','C1','N_style'),('history_vs_diagnostic','C3','N_history')]:
        result[name]={'weights':{a:1,b:-1},'estimand':'simple text-package comparison',
            'control_validity':'N controls require independent semantic validity; length alone insufficient' if b.startswith('N_') else 'different prompt lengths possible'}
    return result

PROFILES={
    'PF_A':{'linguistic':'Brief direct clauses; prefer "noted" as acknowledgment; avoid exclamation marks.',
            'behavioral':'Give the requested answer before optional explanation.',
            'reference_examples':['Noted. The meeting is at ten.','The blue path is open. I checked the sign.']},
    'PF_B':{'linguistic':'Calm complete sentences; use polite acknowledgment; avoid emphatic punctuation.',
            'behavioral':'Acknowledge the request before giving the requested answer.',
            'reference_examples':['Certainly. The meeting is at ten.','I understand. The blue path is open.']},
    'PF_C':{'linguistic':'Use two short parallel clauses separated by a semicolon; no emoji.',
            'behavioral':'When asked to recommend, state a recommendation then one reason.',
            'reference_examples':['Take the blue path; it is shorter.','Choose the morning slot; it is quieter.']}
}

def features(text):
    words=re.findall(r"\b[\w]+(?:['’][\w]+)?\b",text)
    sentences=[s for s in re.split(r'[.!?]+',text) if s.strip()]
    return {'word_count':len(words),'sentence_count':len(sentences),
        'mean_words_per_sentence':len(words)/len(sentences) if sentences else None,
        'semicolons':text.count(';'),'exclamation_marks':text.count('!'),
        'contractions':sum("'" in w or '’' in w for w in words),
        'sufficient_style_opportunity':len(words)>=8,
        'interpretation':'Descriptive cues only, not a Persona Fidelity score.'}

def examples():
    # Authored counterexamples, not observed responses or independent labels.
    base={'evidence':'The trusted note assigns locker L2 to the visitor for the requested date.',
          'question':'Give the assigned locker.', 'task_reference':'L2'}
    items=[
      ('PF_A','Locker L2. Noted.','supported answer; plausible brief style; answer-first'),
      ('PF_A','Locker L9. Noted.','incorrect fact can retain brief style and answer-first'),
      ('PF_A','Noted. I will look that up.','style cue without task delivery'),
      ('PF_A','Certainly! I am absolutely delighted to inform you that your designated locker is L2!','correct answer; mismatched punctuation/rhythm'),
      ('PF_B','Certainly. Your assigned locker is L2.','supported answer; calm style; acknowledgment-first'),
      ('PF_B','Certainly. Your assigned locker is L9.','incorrect fact; calm style retained'),
      ('PF_B','L2.','correct short answer; insufficient linguistic opportunity, behavior cue absent'),
      ('PF_B','Your assigned locker is L2. Certainly.','complete calm sentences; answer-first conflicts with behavioral preference'),
      ('PF_C','Choose the morning slot; it is quieter.','recommendation and reason; both parallel clauses'),
      ('PF_C','It is quieter; choose the morning slot.','linguistic form retained; reversed behavioral order'),
      ('PF_C','Choose the evening slot; it is quieter.','form/order retained; false reason under the supplied evidence'),
      ('PF_C','Choose morning!','partial style evidence and missing requested reason')]
    rows=[]
    for i,(profile,text,purpose) in enumerate(items):
        context=base if profile!='PF_C' else {'evidence':'Morning and evening slots are available. Morning is quieter.',
            'question':'Recommend a slot for a quiet visit and give one reason.','task_reference':'morning + quieter'}
        rows.append({'item_id':f'PFDEV{i+1:02d}','profile_id':profile,'response':text,**context,
            'construction_purpose':purpose,'provenance':'AI_ASSISTED_AUTHORED_COUNTEREXAMPLE_NOT_MODEL_OUTPUT',
            'features':features(text),'human_rating':'','human_reviewer':'','human_timestamp':''})
    return rows

def run():
    registry={'version':'core_SFH_alignment_v1','status':'PROSPECTIVE_NOT_ADOPTED',
        'cells':CELLS,'contrasts':contrasts(),'analysis_unit':'paired case, speaker cluster; template dependence sensitivity',
        'H_none_equals_C0':False,'reason':'Current H_none still includes the fictional persona/style profile.',
        'tracks':{'A':'identical sufficient valid trusted evidence within case','B':'evidence availability interventions, separate analysis'},
        'E_V_registry_unchanged':True,'inference_authorized':0}
    io.save(OUT/'core_estimand_registry_proposed_v1.json',registry)
    io.save(OUT/'fidelity_profiles_authored_v1.json',PROFILES)
    rows=examples();io.save(OUT/'fidelity_counterexamples_authored_v1.json',rows)
    blank=[]
    for r in rows:
        blank.append({'item_id':r['item_id'],'profile':PROFILES[r['profile_id']],
          'question':r['question'],'response':r['response'],
          'linguistic_applicability':'','behavioral_applicability':'','linguistic_rating':'','behavioral_rating':'',
          'linguistic_evidence':'','behavioral_evidence':'','alternative_interpretation':'',
          'reviewer_id':'','independent_before_adjudication':'','decision':'','timestamp':''})
    csvwrite(OUT/'fidelity_blind_review_v1.csv',blank)
    csvwrite(OUT/'quality_separate_panel_v1.csv',[{k:r[k] for k in ('item_id','question','evidence','task_reference','response')}|
             {k:'' for k in ('factual_rating','task_success','required_component_coverage','reviewer_id','decision')} for r in rows])
    print(json.dumps({'contrasts':len(registry['contrasts']),'fidelity_counterexamples':len(rows),'human_ratings':0,'new_inference':0}))

if __name__=='__main__':run()

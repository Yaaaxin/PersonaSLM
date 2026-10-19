"""Prospective construct-separation challenges; authored examples, zero judgments."""
from pathlib import Path
import json
from p1d_design import csvwrite
import p1d_budget_calibration as io

OUT=Path('docs/validation/core_sfh_readiness_v1/fidelity_v2')
PROFILE={'linguistic':'Calm complete sentences with courteous wording and no emphatic punctuation.',
    'behavioral':'Acknowledge the current request before answering; give advice only if advice is requested.',
    'references':['Certainly. Your letter is on the desk.','I understand. The meeting starts at ten.']}

def examples():
    items=[
      ('correct_wrong_style','GATE B!!!',True,True,False,False,'Correct task answer with emphatic fragment; no acknowledgment.'),
      ('wrong_correct_persona','Certainly. Your gate is Gate Z.',False,True,True,True,'Complete wrong answer with calm full sentence and acknowledgment first.'),
      ('correct_complete_persona','Certainly. Your gate is Gate B.',True,True,True,True,'All three constructs align; correctness does not define fidelity.'),
      ('history_recall_behavior_mismatch','Your gate is Gate B. You previously used Gate A. Certainly.',True,True,True,False,
       'Accurate current and historical facts, calm sentences, acknowledgment after answer.'),
      ('persona_preserved_no_task','Certainly. I will check the record for you.',None,False,True,True,
       'Courteous acknowledgment before a promise; promise is not a delivered gate. Factual absence is not Incorrect.'),
      ('quality_improved_persona_erased','Gate B.',True,True,None,False,
       'Compare with the promise: answer delivery improves, expected acknowledgment disappears; short wording gives insufficient LF opportunity.'),
      ('correct_history_only','Certainly. You used Gate A last year.',True,False,True,True,
       'Correct intermediate historical fact, no current gate; demonstrates factual support without task success.'),
      ('correct_fact_unasked_advice','Certainly. Your gate is Gate B. You should cancel the trip.',True,True,True,False,
       'Requested fact delivered but unsolicited advice violates the behavioral target. Advice is not scored as an evidence-backed fact.')]
    return [{'item_id':f'PFD2_{i+1:02d}','challenge':name,'profile':PROFILE,
        'question':'What is my gate for today?','trusted_evidence':'The current trusted record assigns Gate B today. Last year the visitor used Gate A.',
        'response':text,'authored_expected':{'factual_support':facts,'requested_answer_present':task,'linguistic_alignment':lf,
        'behavioral_alignment':bf},'intended_distinction':reason,
        'provenance':'AI_ASSISTED_AUTHORED_CHALLENGE_NOT_MODEL_OUTPUT_NOT_HUMAN_LABEL'}
        for i,(name,text,facts,task,lf,bf,reason) in enumerate(items)]

def panels(rows):
    fidelity=[];quality=[]
    for r in rows:
        fidelity.append({k:r[k] for k in ('item_id','profile','question','response')}|
            {k:'' for k in ('LF_applicability','BF_applicability','linguistic_fidelity','behavioral_fidelity',
                'observed_behavior_choice','LF_evidence','BF_evidence','alternative_score','confidence','suspected_unmasking',
                'reviewer_id','independent_before_adjudication','decision','timestamp')})
        quality.append({k:r[k] for k in ('item_id','question','trusted_evidence','response')}|
            {k:'' for k in ('factual_consistency','temporal_consistency','task_success','component_presence','semantic_completeness',
                'relevance','coherence','evidence_citations','reviewer_id','decision','timestamp')})
    return fidelity,quality

def run():
    rows=examples();f,q=panels(rows)
    io.save(OUT/'authored_challenges_v2.json',rows)
    csvwrite(OUT/'fidelity_blind_panel_v2.csv',f);csvwrite(OUT/'quality_blind_panel_v2.csv',q)
    spec={'version':'fidelity_operational_rubric_proposed_v2','status':'PROPOSED_NOT_HUMAN_VALIDATED',
      'scale':{'1':'Clear repeated incompatibility across available cues','2':'Mostly incompatible cues',
               '3':'Mixed compatible/incompatible cues','4':'Clear alignment with a minor deviation',
               '5':'Clear alignment across available opportunities; not merely copied words'},
      'states':['SCORED','INSUFFICIENT_OPPORTUNITY','BOUNDARY_UNRESOLVED','INTERPRETATION_UNCERTAIN','MISSING','NOT_APPLICABLE'],
      'linguistic_fields':['lexical_choice','sentence_rhythm','punctuation','register'],
      'behavior_fields':['acknowledgment_vs_answer_order','advice_only_when_requested'],
      'no_automatic_scalar':True,'evidence_requirement':'Separate LF/BF spans and an alternative plausible score, independent of correctness.',
      'short_answer_rule':'Do not impose the earlier eight-word heuristic as a scoring threshold. Judge available cues; too little evidence is a state, not score 1.',
      'independence':'Two actual reviewers receive shuffled panels before AI keys; recruit if available. Adoption by researcher is not a second independent annotation.',
      'calibration':'These authored examples can reveal rubric confusion but cannot establish psychometric validity. Revise rubric only prospectively before experimental freeze.',
      'agreement_plan':'Per-dimension ordinal alpha or weighted kappa, state contingency, raw disagreements and speaker-block uncertainty; zero actual agreement estimates here.',
      'validation_stop':'If raters consistently equate facts/task with persona, or cannot distinguish behavior/LF, withhold confirmatory fidelity claims and revise before freeze.',
      'human_reviews':0,'generated_responses':0,'new_authored_challenges':len(rows)}
    io.save(OUT/'rubric_proposed_v2.json',spec)
    print(json.dumps({'authored_challenges':len(rows),'human_reviews':0,'panels':'separate','inference':0}))

if __name__=='__main__':run()

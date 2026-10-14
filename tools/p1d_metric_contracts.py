"""Metric-specific contracts on explicit evidence annotations, never NLP scoring.

Do not feed future validation answers to these development fixtures. Factual,
temporal and task judgments accept separate evidence, not a shared score flag.
Unresolved claims cannot be automatically turned into task failure.
"""
from p1d_design import write, csvwrite
from p1d_scientific_audit import DEST

LABELS={'Correct','Incorrect','Unverifiable'}

def factual_from_claim_checks(checks, boundary_resolved=True):
    if not boundary_resolved: return {'label':'Unverifiable','state':'BOUNDARY_UNRESOLVED'}
    if any(c['support'] not in LABELS for c in checks): raise ValueError('Invalid support category')
    label='Incorrect' if any(c['support']=='Incorrect' for c in checks) else 'Unverifiable' if not checks or any(c['support']=='Unverifiable' for c in checks) else 'Correct'
    return {'label':label,'state':'EVIDENCE_UNVERIFIABLE' if label=='Unverifiable' else 'ASSESSABLE'}

def temporal_from_time_checks(checks, applicable=True, boundary_resolved=True):
    if not applicable:return {'label':'Not Applicable','state':'NOT_APPLICABLE'}
    if not boundary_resolved:return {'label':'Unverifiable','state':'BOUNDARY_UNRESOLVED'}
    # Wrong entity alone supplies no evidence of wrong interval selection.
    if any(c['time_judgment'] not in LABELS for c in checks):raise ValueError('Invalid time category')
    if any(c['time_judgment']=='Incorrect' for c in checks):return {'label':'Incorrect','state':'ASSESSABLE'}
    if not checks or any(c['time_judgment']=='Unverifiable' for c in checks):return {'label':'Unverifiable','state':'INTERPRETATION_UNCERTAIN'}
    return {'label':'Correct','state':'ASSESSABLE'}

def task_from_delivery(components, delivered_answer, material_false_claim=False, unresolved=False, boundary_resolved=True):
    if not boundary_resolved or unresolved or any(x is None for x in components) or delivered_answer is None:
        return 'Uncertain'
    if not components:raise ValueError('Required component set cannot be empty')
    if any(type(x) is not bool for x in components):raise ValueError('Components require explicit support decisions')
    return 'Success' if all(components) and delivered_answer and not material_false_claim else 'Failure'

def ordinal_review(score,evidence,reason,uncertainty,metric):
    if metric not in ('response_relevance','conversational_coherence','persona_fidelity'):raise ValueError('Wrong endpoint')
    if score is not None and (type(score) is not int or not 1<=score<=5):raise ValueError('Ordinal range')
    if score is not None and (not evidence or not reason):raise ValueError('Separate endpoint evidence required')
    if score is None and not uncertainty:raise ValueError('Unscorable reason required')
    return {'metric':metric,'score':score,'evidence':evidence,'reason':reason,'uncertainty':uncertainty}

def main():
    # Abstract authored states, not generated responses or independent ground truth.
    fixtures=[
        ('correct_complete',['Correct'],['Correct'],[True,True],True,False,False,True),
        ('correct_partial',['Correct'],['Correct'],[True,False],True,False,False,True),
        ('incorrect_complete',['Incorrect'],['Incorrect'],[False,False],True,True,False,True),
        ('wrong_entity_unknown_time',['Incorrect'],['Unverifiable'],[False,False],True,True,False,True),
        ('true_historical_not_requested',['Correct'],['Unverifiable'],[False,False],True,False,False,True),
        ('unsupported_complete',['Unverifiable'],['Unverifiable'],[None,None],True,False,True,True),
        ('correct_claims_no_answer',['Correct'],['Correct'],[True,True],False,False,False,True),
        ('boundary_unresolved',[],[],[None,None],None,False,True,False)]
    rows=[]
    for name,fc,tc,components,delivered,false,unknown,boundary in fixtures:
        rows.append({'fixture':name,'provenance':'AUTHORED_CONTRACT_FIXTURE_NOT_HUMAN_OR_MODEL_DATA',
            'factual':factual_from_claim_checks([{'support':x} for x in fc],boundary),
            'temporal':temporal_from_time_checks([{'time_judgment':x} for x in tc],boundary_resolved=boundary),
            'task':task_from_delivery(components,delivered,false,unknown,boundary),
            'delivered_answer':delivered,'supported_components':components,'independent_accuracy':None})
    write(DEST/'metric_construct_contract_fixtures_v1.json',rows)
    write(DEST/'metric_review_contract_v1.json',{
        'policy_source':'docs/validation/p1d/proposed_v1/analysis_policy_proposal_v1.json',
        'changes_to_approved_rubric':False,'independence_claim':'Separate inputs/code paths; no claim of independently produced human ratings or proven construct validity.',
        'review_stages':['Masked relevance pass: question responsiveness/required scope, quote and rubric anchor',
            'Separate masked coherence pass: dialogue continuity/referent resolution/organization, quote and anchor',
            'Claim support pass: subject/predicate/value/asserted date/source IDs/uncertainty',
            'Temporal pass: requested date and interval evidence; wrong entity alone does not prove a temporal error',
            'Task/component pass: delivered requested supported components and material false claims, no copy of factual score',
            'Persona fidelity pass: narrow frozen style target, not task correctness or biography imitation',
            'Boundary pass: unchanged full output after initial semantic assessment; multiple defensible spans allowed'],
        'blank_human_fields':['reviewer_id','actual_review_time','decision','evidence_quotes','reason','alternative_score','uncertainty','adjudication'],
        'required_separate_states':['EVIDENCE_UNVERIFIABLE','BOUNDARY_UNRESOLVED','INTERPRETATION_UNCERTAIN','STRUCTURALLY_UNSCORABLE','MISSING','NOT_APPLICABLE'],
        'do_not_impute':['No reply boundary -> unknown, not false','No annotation -> Missing, not Unverifiable','CROSS_TURN/TRUNCATED alone never sets factual category','Zero variance retained and reported'],
        'readiness':'Independent reviewer and rubric pilot pending. Existing P1c masked 72-item boundary packet retained; no fictional second reviewer.'})
    print({'authored_contract_fixtures':len(rows),'new_human_ratings':0})

if __name__=='__main__':main()

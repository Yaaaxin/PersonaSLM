"""Researcher-label gates, preserving nonbinary labels and full denominators.

This module neither supplies human labels nor issues model requests. A future
confirmation import must preserve the actual researcher message and its bound
annotation snapshot; AI proposals cannot call the conditional fallback ready.
"""
from collections import Counter
import csv
from pathlib import Path
import p1_recovery_v2 as r
s=r.s

LABELS={'Correct':'Success','Success':'Success','Partially correct':'Partially correct',
        'Incorrect':'Failure','Failure':'Failure','Unverifiable':'Uncertain','Uncertain':'Uncertain',
        'Not applicable':'N/A','Not Applicable':'N/A','N/A':'N/A','Missing':'Missing'}


def panel_from_review_csv(path):
    """Prepare an import view only; no confirmation is inferred from a file."""
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    return [x|{'automatic_task_success':x['automatic_score']} for x in rows if x['condition'] in ('D0','D1','D2','D3')]


def decide(rows,confirmed_registration=None):
    pending={'status':'SCIENTIFIC DECISION PENDING REVIEW','selected_configuration':None,'fallback_activated':False}
    if confirmed_registration is None:return pending
    s.require(confirmed_registration.get('researcher')=='Yaxin ZHENG','Wrong decision authority')
    s.require(confirmed_registration.get('decision')=='ANNOTATIONS_CONFIRMED','No annotation adoption')
    source=Path(confirmed_registration['source_message_path'])
    s.require(source.is_file() and s.sha256(source)==confirmed_registration['source_message_sha256'],'Confirmation provenance unavailable')
    snapshot=Path(confirmed_registration['annotation_snapshot_path'])
    s.require(snapshot.is_file() and s.sha256(snapshot)==confirmed_registration['annotation_snapshot_sha256'],'Confirmed snapshot changed')
    s.require(s.load(snapshot)==rows,'Rows differ from confirmed snapshot')
    expected={(c['case_id'],con) for c in r.d.select_cases(r.d.cases()) for con in ('D0','D1','D2','D3')}
    s.require(len(rows)==32 and {(x['case_id'],x['condition']) for x in rows}==expected,'Gate32 paired inventory')
    if any(x.get('record_state') not in ('COMPLETED','ARCHIVED_COMPLETED_REUSED_NO_INFERENCE') or not x.get('researcher_decision') for x in rows):return pending
    groups={con:[x for x in rows if x['condition']==con] for con in ('D0','D1','D2','D3')};counts={}
    for con,items in groups.items():
        s.require(all(x['researcher_decision'] in LABELS for x in items),'Unknown human label; do not coerce')
        human=[LABELS[x['researcher_decision']] for x in items]
        counts[con]={'audited_success':sum(x=='Success' for x in human),
            'automatic_agreement':sum(a==x['automatic_task_success'] for a,x in zip(human,items)),
            'denominator':8,'audited_distribution':dict(Counter(human))}
    chosen=next((con for con,x in counts.items() if x['audited_success']>=6 and x['automatic_agreement']>=7),None)
    return {'status':'QUALIFIED_FOR_PREPARATION_ONLY' if chosen else 'NO_CONFIGURATION_QUALIFIED',
            'selected_configuration':chosen,'condition_counts':counts,'fallback_activated':False,
            'fallback_scientific_prerequisite_met':chosen is None,'pilot_execution_authorized':False}


def fallback_ready(decision,oq_integrity,bank_verified,preflight):
    # A complete negative audited result is necessary, never AI failure alone.
    return bool(decision.get('status')=='NO_CONFIGURATION_QUALIFIED' and decision.get('fallback_scientific_prerequisite_met')
        and oq_integrity.get('attempted')==oq_integrity.get('results')==24 and bank_verified is True
        and preflight.get('status')=='PASS' and preflight.get('requests')==8)


def fallback_result(labels,confirmed=False):
    if not confirmed or len(labels)!=8 or any(x not in LABELS for x in labels):return 'SCIENTIFIC DECISION PENDING REVIEW'
    return 'PREPARE_QUALIFIED_PILOT_ONLY' if sum(LABELS[x]=='Success' for x in labels)>=7 else 'STOP_FORMAL_MODEL_FEASIBILITY_REVIEW'

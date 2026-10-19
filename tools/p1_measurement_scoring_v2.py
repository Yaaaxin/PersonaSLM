"""Versioned metric-independence correction; preserve the pre-run v1 scorer.

This is a measurement implementation correction, not a new scientific rubric.
Closed-form FC and TC in v1 shared a label assignment. V2 computes interval
support separately, and abstains for wrong-entity temporal attribution.
No output-dependent parameter fitting or model inference.
"""
from p1_measurement_scoring import score as original_score, norm, VALUE, STRICT
import re


def canonical_syntax(text):
    if text is None:return None
    # Declared type labels only; preserve dates, negation, qualifiers and prose.
    text=text.replace('**','').replace('`','')
    text=re.sub(r'\b(Bay|Zone|Gate)\s*:\s*([BZG]\d+)',r'\1 \2',text,flags=re.I)
    text=re.sub(r'\b(?:Assigned bay|Bay)\s*[:=]\s*(Bay\s+B\d+)',r'\1',text,flags=re.I)
    text=re.sub(r'\bZone\s*[:=]\s*(Zone\s+Z\d+)',r'\1',text,flags=re.I)
    text=re.sub(r'\bGate\s*[:=]\s*(Gate\s+G\d+)',r'\1',text,flags=re.I)
    text=re.sub(r'\bCollection window\s*[:=]\s*(\d{2}:\d{2}[-–]\d{2}:\d{2})',r'\1',text,flags=re.I)
    return text


def temporal_check(text,c,identifiable):
    if text is None:return 'Missing'
    if not identifiable or not STRICT.fullmatch(text) or c['family']=='dated_comparison':return 'Unverifiable'
    values=VALUE.findall(text)
    if not values:return 'Unverifiable'
    # Relevant entities include the explicitly requested speaker and chain nodes;
    # relevance is resolved from the reference witnesses, not treatment labels.
    by_id={f['source_id']:f for f in c['facts']}
    requested_entities={by_id[s]['entity'] for r in c['reference'] for s in r['source_ids']}
    states=[]
    for value in values:
        matches=[f for f in c['facts'] if norm(f['value'])==norm(value) and f['entity'] in requested_entities]
        if not matches:states.append('Unverifiable')
        elif any(f['valid_from']<=c['requested_date']<=f['valid_to'] for f in matches):states.append('Correct')
        else:states.append('Incorrect')
    return 'Incorrect' if 'Incorrect' in states else 'Unverifiable' if 'Unverifiable' in states else 'Correct'


def score(text,c,identifiable=True):
    canonical=canonical_syntax(text)
    v=original_score(canonical,c,identifiable)
    v['temporal']=temporal_check(canonical,c,identifiable)
    if canonical and re.search(r'\b(not|incorrect|rather than|no longer|formerly|previously)\b',canonical,re.I) and v['task_success']=='Success':
        v['task_success']='Uncertain'
        v['evidence']['scope_review_required']=True
    v['provenance']='DETERMINISTIC_RULE_PROPOSAL_V2_NOT_HUMAN_VALIDATED'
    v['implementation_revision']='Separate temporal validity from factual label; recognize explicitly typed label syntax. Original v1 outputs retained for comparison.'
    v['canonical_syntax_view']=canonical
    return v

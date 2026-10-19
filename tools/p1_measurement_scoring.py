"""Conservative P1 measurement checks; no generation or human adjudication."""
from collections import Counter
import math
import re

VALUE = re.compile(r'\b(?:Bay\s+[BD]\d+|Zone\s+Z\d+|Gate\s+G\d+|\d{2}:\d{2}\s*[-–]\s*\d{2}:\d{2})\b', re.I)
STRICT = re.compile(r'\A\s*(?:(?:Bay\s+[BD]\d+|Zone\s+Z\d+|Gate\s+G\d+|\d{2}:\d{2}[-–]\d{2}:\d{2})[.;,\s]*)+\Z', re.I)
PROMISE = re.compile(r'\b(?:I will|I can|let me|I would need|cannot determine|not enough|not provided|do not know)\b',re.I)


def norm(x):
    return re.sub(r'\s+', ' ', x.replace('–','-')).strip().lower()


def dated_attachment(text,value,month):
    """Narrow: date and value in same clause, no other bay or negation."""
    for clause in re.split(r'[;\n.]',text):
        if norm(value) in norm(clause) and len(re.findall(r'\bBay\s+B\d+',clause,re.I))==1:
            has=bool(re.search('March|2051-03-15' if month==3 else 'September|2051-09-15',clause,re.I))
            opposite=bool(re.search('September|2051-09-15' if month==3 else 'March|2051-03-15',clause,re.I))
            if has and not opposite and not re.search(r'\b(not|instead|incorrect)\b',clause,re.I):return True
    return False


def stale_state(text,c,identifiable=True):
    e=c['stale_endpoint']
    if not e['eligible']:return 'NOT_APPLICABLE'
    if not identifiable:return 'BOUNDARY_UNRESOLVED'
    old,new=e['old_value'],e['current_value']
    if norm(old) not in norm(text):return 'NOT_ADOPTED'
    if dated_attachment(text,old,3) and not dated_attachment(text,old,9):return 'NOT_ADOPTED'
    if dated_attachment(text,old,9):return 'ADOPTED'
    if re.search(r'\b(not|incorrect|previous|previously|formerly|old|earlier|March|2051-03-15)\b',text,re.I):return 'UNVERIFIABLE'
    if c['family']!='dated_comparison' and STRICT.fullmatch(text) and norm(new) not in norm(text):return 'ADOPTED'
    return 'UNVERIFIABLE'


def score(text,c,identifiable=True):
    """Component checking != factuality. Unsupported prose is deferred."""
    if text is None:
        return {k:'Missing' for k in ('factual','temporal','task_success','semantic_completeness','relevance','coherence')}|{'delivered':None,'supported':None,'required':len(c['reference']), 'stale_adoption':'MISSING','linguistic_fidelity':None,'behavioral_fidelity':None}
    values=[norm(x) for x in VALUE.findall(text)]
    refs=[norm(x['value']) for x in c['reference']]
    delivered=sum(any(v.startswith('bay ') for v in values) if 'bay' in r['key'] else
                  any(v.startswith('zone ') for v in values) if r['key']=='connected_zone' else
                  any(v.startswith('gate ') for v in values) if r['key']=='departure_gate' else
                  any(re.match(r'\d{2}:',v) for v in values) for r in c['reference'])
    supported=sum(x in values for x in refs)
    comparison=c['family']=='dated_comparison'
    if comparison:
        delivered=min(2,sum(v.startswith('bay ') for v in values))
        supported=sum(dated_attachment(text,r['value'],3 if r['key']=='march_bay' else 9) for r in c['reference'])
    strict=bool(STRICT.fullmatch(text));extra=set(values)-set(refs);promise=bool(PROMISE.search(text))
    task='Success' if supported==len(refs) and not extra and not promise else 'Failure'
    if comparison and set(refs)<=set(values) and supported<len(refs):task='Uncertain'
    if not identifiable:task='Uncertain'
    completeness='YES' if delivered==len(refs) and not promise else 'NO'
    if comparison and not (re.search('March|2051-03-15',text,re.I) and re.search('September|2051-09-15',text,re.I)):completeness='NO'
    factual=('Incorrect' if extra else 'Correct') if strict and values and not comparison else 'Unverifiable'
    temporal=factual if strict and values and not comparison else 'Unverifiable'
    if not identifiable:factual=temporal='Unverifiable';completeness='UNCERTAIN'
    rr=5 if strict and values else None
    cc=5 if strict and values else None
    lf=bf=None
    style=c['fidelity_target']['linguistic']
    if len(text.split())>=4 and values:
        if 'short direct' in style:lf=5 if len(text.split())<=35 and (';' in text or len(refs)==1) else 3
        else:lf=5 if re.search(r'\b(?:Certainly|Please|assigned|collection|connected)\b',text) and text.rstrip().endswith('.') else 3
    ack=re.search(r'\b(?:Noted|Certainly|Understood|I understand)\b',text,re.I);first=VALUE.search(text)
    if ack and first:
        aligned=(ack.start()>first.start())==(c['fidelity_target']['behavioral']=='answer_then_acknowledgment')
        bf=5 if aligned else 1
    return {'factual':factual,'temporal':temporal,'task_success':task,'delivered':delivered,'supported':supported,'required':len(refs),
        'semantic_completeness':completeness,'relevance':rr,'coherence':cc,'linguistic_fidelity':lf,'behavioral_fidelity':bf,
        'fidelity_state':{'linguistic':'SCORED' if lf is not None else 'INSUFFICIENT_OPPORTUNITY',
                          'behavioral':'SCORED' if bf is not None else 'INSUFFICIENT_OPPORTUNITY'},
        'stale_adoption':stale_state(text,c,identifiable),'boundary_identifiable':identifiable,
        'evidence':{'recognized_values':values,'reference_values':refs,'extra_values':sorted(extra),
                    'restricted_grammar':strict,'date_attachment_requires_review':comparison,'free_prose_claim_audit_required':not strict},
        'provenance':'DETERMINISTIC_RULE_PROPOSAL_NOT_HUMAN_VALIDATED'}


def wilson(success,n,z=1.959963984540054):
    if not n:return None
    p=success/n;den=1+z*z/n;center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [center-half,center+half]


def signed_bounds(weights,values):
    """Fixed weights; unknown binary cells span 0/1 without renormalization."""
    lo=hi=0.
    for key,w in weights.items():
        v=values.get(key)
        if v is None:lo+=min(0,w);hi+=max(0,w)
        else:lo+=w*v;hi+=w*v
    return [lo,hi]


def agreement(left,right):
    pairs=[(a,b) for a,b in zip(left,right) if a is not None and b is not None and a!='Missing' and b!='Missing']
    return {'paired_comparable':len(pairs),'total':len(left),'agreement':sum(a==b for a,b in pairs),
        'agreement_rate':sum(a==b for a,b in pairs)/len(pairs) if pairs else None,
        'confusion':[{'automatic':a,'AI':b,'count':n} for (a,b),n in Counter(pairs).items()],
        'scope':'System agreement, not independent accuracy or human inter-rater reliability.'}

"""Offline localization of parser hazards; known parsing adaptation, not new science.

No generation, evidence, answer key or treatment label enters candidate selection.
Candidates are diagnostic views, never replacements for frozen response_status_v1.
"""
import re
from personaslm.response_status import classify_response, PREFIX, ROLE, UNKNOWN_ROLE, QUOTED_ROLE

def inspect(raw, native):
    frozen=classify_response(raw,native,declared_stops=())
    prefix=PREFIX.match(raw);start=prefix.end() if prefix else 0
    body=raw[start:];roles=list(ROLE.finditer(body))
    first=roles[0].start()+start if roles else None
    markers=[]
    for m in UNKNOWN_ROLE.finditer(body):
        if not ROLE.match(body,m.start()):
            at=start+m.start();markers.append({'type':'unrecognized_line_label','start':at,
                'text':m.group(0),'relative_to_first_role':'before' if first is None or at<first else 'after'})
    for m in QUOTED_ROLE.finditer(body):
        at=start+m.start();markers.append({'type':'quoted_role','start':at,'text':m.group(0),
            'relative_to_first_role':'before' if first is None or at<first else 'after'})
    candidate=None;reason='NO_OBSERVED_ROLE_BOUNDARY'
    if first is not None:
        leading=raw[start:first]
        hazards=[]
        if UNKNOWN_ROLE.search(leading):hazards.append('prefix_line_label')
        if QUOTED_ROLE.search(leading):hazards.append('prefix_quoted_role')
        if '```' in leading or '~~~' in leading:hazards.append('prefix_fence')
        if re.search(r'\b(user|assistant|system|human|bot)[ \t]*:',leading,re.I):hazards.append('prefix_inline_role')
        if 'contradictory_backend_termination' in frozen['reasons']:hazards.append('contradictory_native_stop')
        if not leading.strip():hazards.append('empty_prefix')
        if not hazards:
            candidate={'start':start,'end':first,'text':leading}
            reason='NONEMPTY_PREFIX_BEFORE_FIRST_ANCHORED_ROLE_WITH_NO_PREFIX_HAZARD'
        else:reason='ABSTAIN:'+','.join(hazards)
    return {'original_status':frozen['status'],'original_identifiable':frozen['unit_identifiable'],
        'original_reasons':frozen['reasons'],'first_anchored_role_offset':first,'marker_locations':markers,
        'local_prefix_candidate':candidate,'candidate_reason':reason,
        'independent_boundary_accuracy':None,'classification':'ENGINEERING_ADAPTATION_OF_ROLE_PARSING',
        'limitation':'A role-like line can be quoted document content even without recognized syntax; candidate is not certified ground truth.'}

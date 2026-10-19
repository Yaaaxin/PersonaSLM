"""Encode item-by-item AI review after reading all 32 source outputs/witnesses.
No automatic derivation of AI labels from deterministic scores. Human fields blank.
"""
import json
from pathlib import Path
import p1_measurement_run as r
from p1d_design import csvwrite

# FC, TC, task, delivered, supported, completeness, relevance, coherence, LF, rationale.
RATINGS = {
1:('Incorrect','Incorrect','Failure',1,0,'YES',5,5,None,'B5408 is the January-June bay, not the September bay B5400.'),
2:('Incorrect','Incorrect','Failure',2,0,'YES',5,5,4,'Both the bay B5916 and 09:00-10:00 window are expired for the September question.'),
3:('Correct','Correct','Success',3,3,'YES',5,5,3,'The B5659 -> Z5675 -> G5662 chain matches all September witnesses. Attribute labels are not role transitions.'),
4:('Incorrect','Incorrect','Failure',2,1,'YES',4,4,2,'The March claim and its interval are correct. The explicit September no-assignment claim contradicts E01. The trailing explanation is unfinished; the negative answer is delivered but wrong.'),
5:('Incorrect','Incorrect','Failure',1,0,'YES',5,5,None,'B5052 is valid July-December; the requested March value is B5096.'),
6:('Correct','Correct','Success',1,1,'YES',5,5,None,'B5456 is the unique valid September bay.'),
7:('Incorrect','Incorrect','Failure',1,0,'YES',5,5,None,'B5844 is the expired first-half assignment; September requires B5816.'),
8:('Incorrect','Incorrect','Failure',2,1,'YES',5,5,3,'B6359 is correct; 09:00-10:00 is the expired window instead of 14:00-15:00.'),
9:('Incorrect','Incorrect','Failure',3,0,'YES',5,5,3,'The typed B5270/Z5294/G5273 route belongs to the later interval; March requires B5284/Z5265/G5257.'),
10:('Correct','Correct','Success',2,2,'YES',5,5,3,'B5954 and 09:00-10:00 both apply to the requested March date.'),
11:('Incorrect','Incorrect','Failure',2,0,'YES',4,4,4,'The two correct entity values are attached to the opposite dates. Both requested slots are delivered; truncated reasoning does not repair the reversal.'),
12:('Incorrect','Incorrect','Failure',2,0,'YES',5,5,4,'B6329 and the morning window are valid only before July; both requested September components are wrong.'),
13:('Correct','Correct','Success',1,1,'YES',5,5,None,'B6294 matches the September witness.'),
14:('Correct','Correct','Success',3,3,'YES',5,5,4,'Explicit Bay/Zone/Gate labels deliver the correct B5604/Z5629/G5601 route.'),
15:('Correct','Correct','Success',2,2,'YES',4,4,4,'Both correct requested values are delivered before an unfinished citation. The incomplete citation makes no additional false claim.'),
16:('Incorrect','Incorrect','Failure',1,0,'NO',3,2,2,'B5316 is incorrectly attached to March, followed by acknowledgment that its July interval is not active. No September answer is delivered.'),
17:('Incorrect','Incorrect','Failure',1,1,'NO',3,2,4,'Two incompatible bays are assigned to March without an explicit correction. The second March statement is supported, but September remains unanswered.'),
18:('Correct','Correct','Success',3,3,'YES',5,5,4,'The labeled B6428/Z6436/G6432 chain is correct for September.'),
19:('Incorrect','Incorrect','Failure',2,0,'YES',5,5,3,'The later B5167 and afternoon window are incorrectly used for March.'),
20:('Incorrect','Unverifiable','Failure',2,1,'YES',4,4,2,'D5506 belongs to a different entity. The afternoon window is correct. Wrong-entity attribution is established; an isolated temporal-selection error is not established.'),
21:('Incorrect','Incorrect','Failure',3,0,'YES',5,5,4,'The complete B6049/Z6031/G6010 route is the expired route, not the September route.'),
22:('Incorrect','Incorrect','Failure',3,0,'YES',5,5,3,'The B6490/Z6483/G6456 route is valid in the earlier interval, not September.'),
23:('Correct','Correct','Success',3,3,'YES',5,5,4,'All three labeled September components B5238/Z5201/G5215 are supported.'),
24:('Incorrect','Unverifiable','Failure',2,1,'YES',4,4,2,'March B6523 is correct. September D6507 is a different entity value, not B6507. Temporal attribution is confounded with entity error; retain Unverifiable and an Incorrect alternative.'),
25:('Incorrect','Incorrect','Failure',2,0,'YES',4,4,4,'March and September values are reversed, including the beginning of the supporting explanation.'),
26:('Incorrect','Incorrect','Failure',2,0,'YES',4,4,4,'B6180 and B6157 are attached to the wrong dates. Both slots are supplied, with unfinished rationale.'),
27:('Correct','Correct','Success',3,3,'YES',5,5,3,'B6090/Z6063/G6081 is the correct March route.'),
28:('Incorrect','Incorrect','Failure',1,0,'YES',5,5,None,'B5012 is expired for September, which requires B5022.'),
29:('Correct','Correct','Success',1,1,'YES',5,5,None,'B5859 is valid for March; the newest assignment is not required here.'),
30:('Correct','Correct','Success',1,1,'YES',5,5,None,'B6247 is the valid September assignment.'),
31:('Incorrect','Incorrect','Failure',2,1,'YES',4,4,2,'The bay is correct. The explicit unavailable-window answer is contradicted by the September window row. Requested slots are addressed, although the denial is false and reasoning truncates.'),
32:('Incorrect','Incorrect','Failure',1,0,'NO',3,3,2,'The first answer uses the later bay for March and falsely places March in July-December. The September clause stops before a value.')}


def main():
    dest=r.OUT/'A_C0'/'measurement_v1';rows=r.s.load(dest/'masked_evidence_v1.json');out=[]
    for x in rows:
        n=int(x['review_id'][2:]);fc,tc,task,d,support,complete,rr,cc,lf,basis=RATINGS[n]
        alternative=('A negative answer may be considered an unavailable component rather than delivered content; retain NO completeness as a sensitivity judgment.' if n in (4,31) else
                     'Temporal Incorrect is plausible if all wrong-date entity assignments are treated as temporal inconsistency; do not silently adopt that interpretation.' if n in (20,24) else
                     'A supported March statement coexists with an incompatible March statement; supported-component count does not establish an unambiguous final answer.' if n==17 else
                     'A one-point ordinal difference is plausible; it would not alter the literal reference comparison.' if lf is not None else
                     'A narrow brevity feature can be observed, but the code-only answer provides insufficient broader linguistic opportunity.')
        out.append({'review_id':x['review_id'],'raw_sha256':x['raw_sha256'],'evaluation_text':x['raw_output'],
            'text_view':'Entire existing first-response candidate; no raw text deletion or replacement',
            'boundary_identifiable_proposal':True,'boundary_reason':'No dialogue role transition; field labels and reasoning headings remain within the same response. Native eos/limit and incomplete semantic tails are separate.',
            'factual':fc,'temporal':tc,'task_success':task,'delivered':d,'supported':support,'required':len(x['reference']),
            'semantic_completeness':complete,'relevance':rr,'coherence':cc,'linguistic_fidelity':lf,'behavioral_fidelity':None,
            'fidelity_state':{'linguistic':'SCORED' if lf is not None else 'INSUFFICIENT_OPPORTUNITY','behavioral':'INSUFFICIENT_OPPORTUNITY'},
            'stale_adoption':'NOT_APPLICABLE','evidence':x['reference'],'claim_and_task_reason':basis,
            'relevance_reason':'Direct slot response.' if rr==5 else 'Requested content is partly supplied with avoidable explanation or omission.',
            'coherence_reason':'Clear internally connected typed answer.' if cc==5 else 'Unfinished explanatory tail.' if cc==4 else 'Explicit internal date/assignment contradiction and incomplete delivery.',
            'fidelity_reason':'Brief labels show some surface features but do not demonstrate behavioral ordering; long explanations conflict with the brief profile. Neutral complete sentences only partly establish courteous identity.',
            'uncertainty':'Interpretation uncertainty' if n in (4,17,20,24,31) else 'Ordinal/fidelity proposal uncertainty; categorical evidence comparison clear',
            'alternative':alternative,'human_adjudication_required':True,'researcher_decision':'','human_timestamp':None,
            'provenance':'AI_ASSISTED_ITEM_REVIEW_NOT_HUMAN_CONFIRMED; C0 known; no independent reviewer',
            'source_masked_file_sha256':r.s.sha256(dest/'masked_evidence_v1.json')})
    r.s.save(dest/'AI_proposals_UNCONFIRMED_v1.json',out);csvwrite(dest/'AI_proposals_UNCONFIRMED_v1.csv',out)
    print(json.dumps({'records':len(out),'task_success':sum(x['task_success']=='Success' for x in out),'human_ratings':0}))


if __name__=='__main__':main()

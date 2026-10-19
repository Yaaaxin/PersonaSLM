"""Literal AI item judgments after masked inspection of sixteen diagnostic outputs."""
import json
import p1_measurement_run as r
from p1d_design import csvwrite

# Independently reviewed categorical, component and narrow fidelity proposals.
RATINGS={
1:('Incorrect','Incorrect','Failure',3,0,4,'The explicit September row supplies the expired B5212/Z5204/G5217 route.'),
2:('Incorrect','Incorrect','Failure',1,0,None,'B5052 belongs to July-December, not the requested March interval.'),
3:('Incorrect','Incorrect','Failure',2,0,3,'Both B5167 and the afternoon window are from the later interval; March requires B5177 and the morning window.'),
4:('Correct','Correct','Success',3,3,3,'The date and all three March route components match the evidence witnesses.'),
5:('Incorrect','Incorrect','Failure',2,1,4,'B5102 is correct for September, but the morning collection window is expired.'),
6:('Incorrect','Incorrect','Failure',2,0,4,'The two entity values are explicitly assigned to opposite dates. Complete sentences are not correct answers.'),
7:('Incorrect','Incorrect','Failure',2,0,3,'March receives the later bay B5361; September receives another entity value D5356. At least one explicit temporal contradiction exists.'),
8:('Correct','Correct','Success',3,3,3,'All three concise March route components are supported.'),
9:('Incorrect','Incorrect','Failure',2,1,4,'The current bay is correct; the provided window is the expired morning value.'),
10:('Incorrect','Incorrect','Failure',1,0,None,'B5012 is expired for the September request.'),
11:('Correct','Correct','Success',3,3,4,'All three concise September route components match the trusted evidence.'),
12:('Incorrect','Incorrect','Failure',1,0,None,'B5052 is not yet valid on the requested March date.'),
13:('Incorrect','Incorrect','Failure',2,0,3,'The later bay and later window are used for March.'),
14:('Incorrect','Incorrect','Failure',1,0,None,'The answer gives the first-half bay instead of B5022 for September.'),
15:('Incorrect','Incorrect','Failure',2,0,4,'March is assigned B5316 from the later interval; September D5307 belongs to another entity and an earlier interval.'),
16:('Incorrect','Incorrect','Failure',2,0,4,'B5316 and B5341 are reversed across the two dates. The sentences are clear and complete but wrong.')}


def main():
    dest=r.OUT/'C_DIAGNOSTIC'/'measurement_v1';rows=r.s.load(dest/'masked_evidence_v1.json');out=[]
    for x in rows:
        n=int(x['review_id'][2:]);fc,tc,task,d,support,lf,basis=RATINGS[n]
        out.append({'review_id':x['review_id'],'raw_sha256':x['raw_sha256'],'evaluation_text':x['raw_output'],
            'text_view':'Whole original first-response candidate; no text replacement',
            'boundary_identifiable_proposal':True,'boundary_reason':'One native-EOS response; dates and field labels do not introduce another conversation role.',
            'factual':fc,'temporal':tc,'task_success':task,'delivered':d,'supported':support,'required':len(x['reference']),
            'semantic_completeness':'YES','relevance':5,'coherence':5,'linguistic_fidelity':lf,'behavioral_fidelity':None,
            'fidelity_state':{'linguistic':'SCORED' if lf is not None else 'INSUFFICIENT_OPPORTUNITY','behavioral':'INSUFFICIENT_OPPORTUNITY'},
            'stale_adoption':'NOT_APPLICABLE','evidence':x['reference'],'claim_and_task_reason':basis,
            'relevance_reason':'All requested answer slots directly addressed without digression.',
            'coherence_reason':'Clear self-contained answer with no internal discourse break; external factual error scored separately.',
            'fidelity_reason':'Narrow surface alignment only. Brief field rows partly match directness; courteous full-sentence profiles are incompletely expressed. No acknowledgment ordering opportunity.',
            'uncertainty':'Categorical evidence comparison clear; ordinal/fidelity interpretation uncertain.',
            'alternative':'A one-point LF difference is plausible; code-only replies remain insufficient opportunity. No claim of independently validated fidelity.',
            'human_adjudication_required':True,'researcher_decision':'','human_timestamp':None,
            'provenance':'AI_ASSISTED_ITEM_REVIEW_NOT_HUMAN_CONFIRMED; instruction-arm labels masked; output layout can reveal arm',
            'source_masked_file_sha256':r.s.sha256(dest/'masked_evidence_v1.json')})
    r.s.save(dest/'AI_proposals_UNCONFIRMED_v1.json',out);csvwrite(dest/'AI_proposals_UNCONFIRMED_v1.csv',out)
    print(json.dumps({'records':len(out),'success':sum(x['task_success']=='Success' for x in out),'human_confirmations':0}))


if __name__=='__main__':main()

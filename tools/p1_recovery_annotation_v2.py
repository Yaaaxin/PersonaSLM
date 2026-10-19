"""Recorded manual AI review of the masked 32-item view; no model calls.

Labels below were written item by item after reading raw text and evidence,
before opening condition mapping or computing automatic scores. They are not
independent human ratings. Existing D0 recommendations remain authoritative
as unconfirmed source proposals and are never overwritten by reinspection.
"""
import json
import p1_recovery_v2 as r

s,OUT=r.s,r.OUT
# id: task, factual, temporal, answer form, delivered, supported, relevance,
# coherence, overlapping failure tags, claim-level reason, alternative.
ITEMS={
1:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['OUTDATED_VALUE_SELECTED'], 'Ada is assigned B5022 in July–December (E01); B5012 belongs to January–June (E00), before the requested September date. A single answer is delivered but is wrong.', 'A historically true value becomes incorrect when asserted as the September answer.'),
2:('Success','Correct','Correct','YES',1,1,5,5,[], 'Dale B5177 is supported by E00 for March 15. The one requested bay is delivered without additional claims.', 'Shortness does not establish persona fidelity; it satisfies this single-answer request.'),
3:('Success','Correct','Correct','YES',1,1,5,5,[], 'Ada B5022 is supported by E01 for September 15. The complete single-answer requirement is met.', 'An answer code can be semantically complete even where the frozen structural parser is uncertain.'),
4:('Success','Correct','Correct','YES',1,1,5,5,[], 'Glen B5316 is supported by E01 for September 15; only September is requested here.', 'Do not demand the March answer from the original two-date task.'),
5:('Success','Correct','Correct','YES',1,1,5,5,[], 'Glen B5316 matches E01 and its July–December interval covers September 15. The requested single answer is supplied.', 'No claim about the unrequested historical date is made.'),
6:('Success','Correct','Correct','YES',2,2,5,5,[], 'Dale E00 gives B5177 and E02 gives 09:00–10:00; both intervals cover March 15. Both requested components are delivered.', 'Line labels describe answer attributes rather than speaker-role transitions.'),
7:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Bryn B5052 (E01) starts July 1; the March answer is B5096 (E00). The output is complete but date-inappropriate.', 'The latest value is not the correct historical-date answer.'),
8:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['OUTDATED_VALUE_SELECTED'], 'Evan B5212 (E00) expires June 30. The requested September answer is B5238 (E01). One wrong answer is nevertheless fully delivered.', 'No inference about an internal retrieval mechanism is supported.'),
9:('Failure','Incorrect','Incorrect','NO',1,1,4,3,['WRONG_DATE_ATTACHMENT','SELF_CONTRADICTION','INCOMPLETE_ANSWER_COMPONENTS'], 'Hope is first assigned B5361 to March, contradicting its July–December interval, then B5356 is assigned to March correctly. No explicit September answer is delivered; E00/E01 resolve the dates.', 'The second statement might be read as an implicit correction, but the contradiction is not explicitly withdrawn and the September requirement remains unmet.'),
10:('Success','Correct','Correct','YES',1,1,5,5,[], 'Cora B5102 is supported by E01 on September 15. The requested bay is fully delivered.', 'The collection window is not requested by this question.'),
11:('Failure','Incorrect','Incorrect','YES',3,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Faye output follows the July route B5270→Z5294→G5273 (E01/E03/E05), whereas March requires E00/E02/E04: B5284→Z5265→G5257. All three slots are filled but none meets the requested date.', 'Relational consistency of the later route does not make it the correct March answer.'),
12:('Success','Correct','Correct','YES',2,2,5,4,['INCOMPLETE_REASONING_TAIL'], 'Hope March B5356 and September B5361 are explicitly and correctly attached to their dates (E00/E01). The stated first interval is correct. The trailing “This assignment” is incomplete commentary after both required answers.', 'A whole-utterance syntactic completeness rubric could mark the tail incomplete; the existing answer-form criterion counts the two delivered answers. Human adjudication is requested.'),
13:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Faye B5270 (E01) is valid only from July; March requires B5284 (E00). A single incorrect answer is delivered.', 'The wrong date is explicit in the question context even though the code itself has no date.'),
14:('Failure','Incorrect','Incorrect','YES',3,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'The abbreviated Faye route B5270/Z5294/G5273 is the later E01/E03/E05 route. March requires B5284/Z5265/G5257 (E00/E02/E04). All three components are present but wrong for March.', 'Attribute labels make the abbreviated codes unambiguous; they are not missing merely because Bay/Zone/Gate is not repeated.'),
15:('Success','Correct','Correct','YES',3,3,5,5,[], 'Evan September route B5238→Z5201→G5215 matches E01/E03/E05, all valid at the requested date. All three requested components are supplied.', 'Answer field labels are not conversation turns.'),
16:('Success','Correct','Correct','YES',1,1,5,5,[], 'Ada B5022 is the E01 September value and is the sole requested component.', 'This does not test multi-component task delivery.'),
17:('Success','Correct','Correct','YES',1,1,5,5,[], 'Hope B5361 is valid in September according to E01. The single requested answer is supplied.', 'The narrower question does not require the March comparison.'),
18:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Bryn March requires B5096 (E00), while the supplied B5052 is the July–December E01 value.', 'Using the evaluation-date value instead of the requested historical date would be an error, not an alternative accepted answer.'),
19:('Success','Correct','Correct','YES',1,1,5,5,[], 'Bryn B5096 is E00, valid at March 15, and fully answers the single bay question.', 'No inference about general date reasoning follows from one correct selection.'),
20:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['OUTDATED_VALUE_SELECTED'], 'Cora B5101 (E00) expired June 30; September requires B5102 (E01). One complete wrong answer is supplied.', 'The old fact remains historically true but is wrong as the current answer.'),
21:('Success','Correct','Correct','YES',1,1,5,5,[], 'Dale B5177 matches E00 on March 15; the one requested component is present.', 'No collection window is requested here.'),
22:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Faye B5270 is the later E01 assignment, not March B5284 from E00. The answer form is complete.', 'A valid later fact is incorrect in this historical-date response.'),
23:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Bryn B5052 is E01 for July–December, while the question asks March and E00 establishes B5096.', 'This is wrong interval selection, not evidence insufficiency.'),
24:('Success','Correct','Correct','YES',3,3,5,5,[], 'Evan B5238/Z5201/G5215, explicitly labeled by attribute, matches the September E01/E03/E05 chain. All requested components are present.', 'Codes are interpretable with their field labels; repeated entity-type words are unnecessary.'),
25:('Success','Correct','Correct','YES',1,1,5,5,[], 'Evan B5238 is E01 and is valid on September 15. The selected bay component is fully answered.', 'Zone and gate are not requested under this single-component question.'),
26:('Failure','Incorrect','Incorrect','YES',1,0,5,5,['OUTDATED_VALUE_SELECTED'], 'Ada B5012 is E00, which expires before September; E01 supplies the required B5022.', 'The answer is complete in form despite factual and temporal error.'),
27:('Failure','Incorrect','Incorrect','YES',2,0,5,5,['NOT_YET_VALID_VALUE_SELECTED'], 'Dale B5167 and 14:00–15:00 are July–December E01/E03 values. March requires B5177 and 09:00–10:00 (E00/E02). Both components are delivered but wrong.', 'Bold formatting does not affect semantic answer delivery.'),
28:('Failure','Incorrect','Incorrect','NO',1,0,4,3,['WRONG_DATE_ATTACHMENT','SELF_CONTRADICTION','INCOMPLETE_ANSWER_COMPONENTS'], 'Glen B5316 is incorrectly asserted for March while the output itself acknowledges the July interval has not started. E00 establishes March B5341. No explicit September answer is completed.', 'Correctly reciting a July interval does not repair the false March assignment.'),
29:('Failure','Incorrect','Incorrect','YES',2,1,4,4,['FALSE_UNAVAILABILITY','INCOMPLETE_REASONING_TAIL'], 'Cora September B5102 is correct (E01), but “Collection Window: N/A (Not available)” contradicts E03, which supplies 14:00–15:00. The evidence citation tail is incomplete.', 'A false unavailability response can be counted as a delivered but wrong component; alternatively a reviewer may regard the window as undelivered. Original source recommendation must be preserved.'),
30:('Success','Correct','Correct','YES',1,1,5,5,[], 'Hope B5361 matches E01 for September 15 and supplies the one requested answer.', 'No persona behavior can be inferred from the code alone.'),
31:('Success','Correct','Correct','YES',2,2,5,4,['INCOMPLETE_REASONING_TAIL'], 'Glen March B5341 and September B5316 are explicitly attached to the correct dates (E00/E01); the stated January–June interval is correct. “This assignment is” is an unfinished explanatory tail after complete task delivery.', 'Syntactic completeness could be judged NO under a different rubric; under the frozen answer-delivery criterion both answers are complete. Keep this for human adjudication.'),
32:('Failure','Incorrect','Incorrect','YES',2,0,5,5,['OUTDATED_VALUE_SELECTED','OUTDATED_COMPONENT_SELECTED'], 'Cora B5101 and 09:00–10:00 are January–June E00/E02 values. September requires B5102 and 14:00–15:00 (E01/E03). Both wrong components are delivered.', 'A coherent declarative sentence can be factually wrong; coherence is not factual correctness.'),
}


def freeze_masked():
    masked=s.load(OUT/'masked_semantic_view_v2.json');rows=[]
    for x in masked:
        item=ITEMS[int(x['review_id'][2:])]
        keys=['task_success','factual','temporal','semantic_completeness','delivered','supported','relevance','coherence','failure_types','reason','alternative']
        row=dict(zip(keys,item));row.update(review_id=x['review_id'],raw_sha256=x['raw_sha256'],
            evidence_source_ids=[f['source_id'] for f in x['facts']],
            uncertainty='AI-only interpretation. Direct claim/date comparison is supported; no independent reviewer. Original boundary uncertainty remains; answer form and unfinished commentary require human review where noted.',
            boundary_interpretation='Raw continuation is the single answer candidate; no explicit role transition found. Frozen parser status remains unchanged.',
            first_answer_candidate_recoverable=True,linguistic_fidelity=None,behavioral_fidelity=None,
            fidelity_state='NOT_MEASURABLE_IN_THIS_C0_DIAGNOSTIC',
            provenance='Manual item-level assistant assessment of masked view; not an independent human annotation. Label masking does not remove Q-form or familiar-source cues.',
            researcher_decision='',researcher_notes='')
        rows.append(row)
    path=OUT/'masked_AI_reinspection_UNCONFIRMED_v2.json';s.save(path,rows)
    s.save(OUT/'AI_review_provenance_v2.json',{'masked_view_sha256':s.sha256(OUT/'masked_semantic_view_v2.json'),
        'assessment_sha256':s.sha256(path),'recorded_by_software_utc':s.b.utc_now(),'human_review_timestamp':None,
        'independent_human_annotators':0,'researcher_confirmed_records':0,'source':'Current assistant item-by-item reading, no external scorer model calls',
        'masking_limits':'Question cardinality and familiar archived outputs can reveal assignment. The assistant had constructed stimuli and knew earlier outcomes. Not independent blind validation.',
        'D0_policy':'Immutable original recommendations remain in the reviewer CSV; this new reinspection is retained separately.'})
    return {'masked_items':len(rows),'assessment_sha256':s.sha256(path)}


def join():
    # Separate action: do not consult the protected map before freezing labels.
    rows=s.load(OUT/'masked_AI_reinspection_UNCONFIRMED_v2.json');p=s.load(OUT/'AI_review_provenance_v2.json')
    s.require(s.sha256(OUT/'masked_AI_reinspection_UNCONFIRMED_v2.json')==p['assessment_sha256'],'Assessment changed before join')
    mapping={x['review_id']:x for x in s.load(OUT/'protected_condition_mapping_v2.json')}
    s.save(OUT/'AI_proposals_UNCONFIRMED_v2.json',[x|mapping[x['review_id']] for x in rows])
    return {'joined':len(rows),'human_ratings':0}


if __name__=='__main__':
    import sys
    print(json.dumps({'freeze':freeze_masked,'join':join}[sys.argv[1]](),indent=2))

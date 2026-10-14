"""Post-hoc boundary sensitivity; frozen primary parser/results remain untouched."""
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path
import p1c_semantic_review as a

B_SOURCE=a.ROOT/'measurement_v1/structural_review_view_v1.csv'
OUT=a.OUT/'stage_b'
DECISIONS={
 'PC010':('Correct','Correct',1,1.0,5,5,'The opening Orchid/Thursday assertion is supported. The header asks a new music-label question, followed by an additional Assistant answer. Do not use that later music answer.'),
 'PC023':('Correct','Correct',1,1.0,4,4,'The opening supplies Orchid and Thursday; the repeated question and later answer are continuation. "on a Thursday" is interpreted as service-day wording; confirm that interpretation separately.'),
 'PC033':('Incorrect','Unverifiable',0,.5,5,5,'The opening supplies Silver/Tuesday. Tuesday is supported, but the required desk is Maple; Silver belongs to the colleague. The later Assistant turn is incomplete and cannot repair this answer.'),
 'PC039':('Incorrect','Unverifiable',0,0.0,5,5,'The opening supplies Silver/Friday rather than Maple/Tuesday. Friday has no trusted ledger support; entity substitution and unsupported day prevent identifying a valid target interval. The trailing Assistant turn cuts off inside Silver.'),
 'PC042':('Incorrect','Unverifiable',0,0.0,5,5,'The opening supplies Silver/Friday rather than Maple/Tuesday. The later Assistant turn ends after a conjunction and quote; evaluate neither it nor an invented completion.'),
 'PC044':('Correct','Correct',1,1.0,5,5,'The opening supplies Maple/Tuesday. RECENT CONVERSATION then reproduces the fixed context and user question, ending in an incomplete role label. The first answer itself has a closed sentence.'),
 'PC054':('Incorrect','Incorrect',0,0.0,5,5,'The opening asserts Silver for June 15, but route 62 then requires Cobalt; Silver is route 61 from the earlier target interval. The following context replay and partial answer are excluded.'),
 'PC063':('Correct','Correct',1,1.0,5,5,'The opening supplies Laurel for December 15. A repeated USER QUESTION and multiple Assistant continuations follow; the final continuation is unfinished, not the initial answer.')}


def stage_b():
    a.require(not OUT.exists(),'Preserve previous boundary versions')
    frozen=a.read(a.OUT/'stage_a/freeze_manifest_v1.json')
    for name,digest in frozen['files'].items():a.require(a.sha(a.OUT/'stage_a'/name)==digest,'Stage A snapshot changed')
    primary=a.read(a.OUT/'stage_a/semantic_proposals_UNCONFIRMED_v1.json')
    structural={r['anonymous_response_id']:r for r in a.rows(B_SOURCE)}
    ambiguous={rid for rid,r in structural.items() if r['frozen_structural_status']=='AMBIGUOUS'}
    a.require(ambiguous==set(DECISIONS),'Unexpected ambiguous inventory')
    boundaries=[];sensitivity=[]
    for row in primary:
        rid=row['anonymous_response_id'];s=structural[rid];r=dict(row)
        a.require(row['raw_first_reply']==s['raw_first_reply'] and row['first_reply_sha256']==s['first_reply_sha256'],'Stage A/B span mismatch')
        if rid in DECISIONS:
            raw=s['raw_full_continuation'];trace=json.loads(s['parser_trace'])
            a.require(a.text_sha(raw)==s['raw_text_sha256'],'Raw continuation hash differs')
            markers=[m for m in ('\n\nUSER QUESTION:\n','\n\nRECENT CONVERSATION:\n') if m in raw]
            a.require(len(markers)==1 and not trace['unit_identifiable'],'Boundary assumptions differ')
            end=raw.index(markers[0]);start=trace['first_span']['start'];view=raw[start:end]
            a.require(bool(view.strip()) and end<trace['first_span']['end'],'No defensible candidate prefix')
            factual,temporal,success,coverage,relevance,coherence,reason=DECISIONS[rid]
            rating={'factual_consistency':factual,'temporal_consistency':temporal,'response_relevance':relevance,
                    'conversational_coherence':coherence,'task_success':success,'component_coverage':coverage,'semantic_completeness':'YES'}
            boundaries.append({'anonymous_response_id':rid,'anonymous_case_id':row['anonymous_case_id'],
                'original_structural_status':s['frozen_structural_status'],'original_unit_identifiable':False,
                'raw_full_continuation':raw,'raw_text_sha256':s['raw_text_sha256'],
                'original_candidate_view':row['raw_first_reply'],'original_candidate_sha256':row['first_reply_sha256'],
                'original_parser_trace':trace,'native_termination':json.loads(s['native_termination']),
                'actual_generated_tokens':int(s['generated_tokens']),'proposed_start':start,'proposed_end':end,
                'proposed_evaluation_view':view,'proposed_view_sha256':a.text_sha(view),'proposed_excluded_continuation':raw[end:],
                'boundary_evidence':reason,'AI_recoverability':'PLAUSIBLE_FOR_SECONDARY_EVALUATION_NOT_CERTIFIED',
                'alternative_interpretation':'The entire continuation may be one generated document rather than properly attributed dialogue. The exact heading is not a native turn token; retain the primary unscorable disposition unless separately adjudicated.',
                'semantic_evaluability_effect':'A secondary answer prefix is available for all seven dimensions; primary status and unit remain unchanged.',
                'AI_secondary_ratings':rating,'AI_source_quotations':a.supporting_quotes(row),
                'temporal_adjudication':('Unverifiable is proposed because wrong-entity/unsupported values do not identify temporal selection. A false date-bound assertion interpretation could instead yield Incorrect.' if temporal=='Unverifiable' else 'Verify date-specific target facts; no newest-fact default.'),
                'AI_recommendation':'RETAIN_PRIMARY_AND_REVIEW_SECONDARY_PREFIX','researcher_boundary_decision':'',
                'researcher_boundary_correction':'','researcher_id':'','review_timestamp':''})
            r.update({'AI_'+k:v for k,v in rating.items()})
            r['secondary_evaluation_view']=view;r['secondary_view_sha256']=a.text_sha(view)
            r['secondary_reason']=reason;r['secondary_status']='BOUNDARY_RECOVERY_PROPOSED'
        else:
            r['secondary_evaluation_view']=row['raw_first_reply'];r['secondary_view_sha256']=row['first_reply_sha256']
            r['secondary_reason']='Identical to frozen primary span and Stage A proposal.';r['secondary_status']='UNCHANGED'
        r['sensitivity_version']='p1c_heading_prefix_sensitivity_v1_POST_HOC'
        sensitivity.append(r)
    a.write_csv(OUT/'ambiguous_boundary_review_UNCONFIRMED_v1.csv',boundaries)
    a.write(OUT/'ambiguous_boundary_review_UNCONFIRMED_v1.json',boundaries)
    a.write(OUT/'boundary_sensitivity_proposals_UNCONFIRMED_v1.json',sensitivity)
    a.write_csv(OUT/'boundary_sensitivity_proposals_UNCONFIRMED_v1.csv',sensitivity)
    a.write(OUT/'boundary_sensitivity_policy_v1.json',{'version':'p1c_heading_prefix_sensitivity_v1','status':'POST_HOC_DIAGNOSTIC_UNCONFIRMED',
        'primary_parser_unchanged':'response_status_v1','applicable_records':sorted(DECISIONS),
        'view':'For eight frozen ambiguous records only, preserve the literal prefix before the first observed double-newline USER QUESTION or RECENT CONVERSATION heading. Keep exact offsets and bytes; never select a later answer.',
        'selection':'All eight ambiguous records retained, irrespective of proposed answer correctness. The rule was specified after these outputs were observed.',
        'limitations':'This is not a generally validated parser, repaired generation, native stop policy or newly invented first reply. No improvement on independent data is established.',
        'human_approval':'Required before treating secondary views/ratings as confirmed; no change to primary estimand.'})
    def summary(rs):
        return {k:dict(Counter('Missing' if r['AI_'+k] is None else str(r['AI_'+k]) for r in rs)) for k in a.FIELDS}
    joint=[]
    for rid,s in structural.items():
        p=next(r for r in primary if r['anonymous_response_id']==rid)
        q=next(r for r in sensitivity if r['anonymous_response_id']==rid)
        joint.append({'anonymous_response_id':rid,'structural_status':s['frozen_structural_status'],
            'native_stop_type':json.loads(s['native_termination'])['stop_type'],
            'primary':{k:p['AI_'+k] for k in a.FIELDS},'secondary':{k:q['AI_'+k] for k in a.FIELDS}})
    a.write(OUT/'measurement_bias_diagnostics_UNCONFIRMED_v1.json',{'status':'AI_PROPOSALS_ONLY_NO_CONDITION_EFFECTS',
        'primary':summary(primary),'secondary':summary(sensitivity),'paired_boundary_rows':joint,
        'primary_unscorable':8,'secondary_recoveries_proposed':8,'official_human_scores':0,
        'naive_strict_complete_as_success':{'COMPLETE':0,'warning':'Equating this count with task success would erase all proposed correct first replies; this is not a valid metric.'}})
    a.write(OUT/'freeze_manifest_v1.json',{'version':'p1c_stage_b_freeze_v1','created_utc':datetime.now(timezone.utc).isoformat(),
        'stage_a_manifest_sha256':a.sha(a.OUT/'stage_a/freeze_manifest_v1.json'),'structural_source_sha256':a.sha(B_SOURCE),
        'files':{p.name:a.sha(p) for p in OUT.iterdir()},'code_sha256':a.sha(__file__),
        'protected_treatment_mapping_accessed':False,'human_confirmation_count':0,'new_generations':0})
    return {'ambiguous_records_reviewed':8,'primary':summary(primary),'secondary':summary(sensitivity),'human_confirmation_count':0}


if __name__=='__main__':print(json.dumps(stage_b(),indent=2))

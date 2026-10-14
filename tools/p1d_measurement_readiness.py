"""Prepare independent boundary audit material from existing P1c development text.

No reviewer, ratings, approval or independent empirical replication is invented.
"""
import csv
import random
from pathlib import Path
from p1d_design import read, write, csvwrite, sha, th

SOURCE = Path('docs/validation/p1c/calibration_v1/measurement_v1')
DEST = Path('docs/validation/p1d/development_readiness_v1/independent_measurement')
SEED = 716501

def csvread(p):
    with p.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def main():
    semantic = {r['anonymous_response_id']:r for r in csvread(SOURCE/'semantic_scoring_view_v1.csv')}
    structural = {r['anonymous_response_id']:r for r in csvread(SOURCE/'structural_review_view_v1.csv')}
    if set(semantic)!=set(structural) or len(semantic)!=72:
        raise ValueError('Original review identity mismatch')
    # Bind to previously audited exact source files, not merely summaries.
    seal=read('docs/validation/p1c/confirmed_semantic_v1/reproducibility_manifest_v1.json')
    for p in (SOURCE/'semantic_scoring_view_v1.csv',SOURCE/'structural_review_view_v1.csv'):
        # Source hash may be nested in the upstream measurement manifest; raw text hashes below are always checked.
        if p.as_posix() in seal['artifact_sha256'] and sha(p)!=seal['artifact_sha256'][p.as_posix()]:
            raise ValueError('Original source changed')
    ids=sorted(semantic);random.Random(SEED).shuffle(ids)
    review=[];mapping=[]
    for index,old_id in enumerate(ids,1):
        s=semantic[old_id];b=structural[old_id]
        if th(b['raw_full_continuation'])!=b['raw_text_sha256'] or th(s['raw_first_reply'])!=s['first_reply_sha256']:
            raise ValueError('Original raw text hash mismatch')
        rid=f'MB{index:03d}'
        review.append({'review_id':rid,'current_question':s['current_question'],
            'fixed_preceding_context':s['fixed_preceding_context'], 'unchanged_raw_continuation':b['raw_full_continuation'],
            'raw_text_sha256':b['raw_text_sha256'], 'character_length':len(b['raw_full_continuation']),
            'accepted_spans_json':'','boundary_disposition':'','answer_delivered':'',
            'supporting_boundary_cues':'','alternative_interpretations':'','uncertainty':'',
            'reviewer_id':'','reviewer_independence_declaration':'','actual_submission_timestamp':''})
        mapping.append({'review_id':rid,'original_anonymous_response_id':old_id,'original_anonymous_case_id':s['anonymous_case_id'],
            'original_parser_status':b['frozen_structural_status'],'original_first_reply_sha256':s['first_reply_sha256'],
            'source_row_hash':th(str(b)), 'raw_text_sha256':b['raw_text_sha256']})
    csvwrite(DEST/'boundary_review_blinded_v1.csv',review)
    write(DEST/'withheld_mapping_v1.json',mapping)
    write(DEST/'provenance_v1.json',{'version':'p1d_measurement_preparation_v1','population':'72 existing P1c development outputs, not new P1d validation data',
        'seed':SEED,'source_files':{(SOURCE/n).as_posix():sha(SOURCE/n) for n in ('semantic_scoring_view_v1.csv','structural_review_view_v1.csv')},
        'reviewer_file_sha256':sha(DEST/'boundary_review_blinded_v1.csv'),'mapping_sha256':sha(DEST/'withheld_mapping_v1.json'),
        'rows':72,'human_ratings':0,'reviewer_recruited':False,'condition_assignments_accessed':False,
        'masking':'Hide model, treatment, parser status, original span, prior ratings and automated predictions. Response text may contain cues.',
        'mapping_access':'Withhold from reviewer; directory separation is not an operating-system access-control guarantee',
        'code_sha256':sha(__file__)})
    print({'blinded_boundary_records':72,'human_ratings':0,'new_generations':0})

if __name__=='__main__':main()

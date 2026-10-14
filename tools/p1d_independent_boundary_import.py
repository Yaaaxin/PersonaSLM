"""Validate a returned human boundary file without inventing or adopting ratings.

Validation is not proof that a declaration is truthful and does not rewrite P1c.
"""
import csv
import json
from pathlib import Path
from p1d_design import th

REVIEW=Path('docs/validation/p1d/development_readiness_v1/independent_measurement/boundary_review_blinded_v1.csv')
FIXED=('review_id','current_question','fixed_preceding_context','unchanged_raw_continuation','raw_text_sha256','character_length')
DECISIONS={'UNIQUE_DEFENSIBLE_SPAN','MULTIPLE_DEFENSIBLE_SPANS','NO_RECOVERABLE_REPLY','UNRESOLVED'}

def read_rows(path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def validate_returned(returned, original=None):
    original=read_rows(REVIEW) if original is None else original
    expected={r['review_id']:r for r in original}
    if len(expected)!=len(original) or len(returned)!=len(original) or len({r['review_id'] for r in returned})!=len(returned):
        raise ValueError('Duplicate or missing review records')
    if {r['review_id'] for r in returned}!=set(expected):raise ValueError('Review identity mismatch')
    result=[]
    for r in returned:
        before=expected[r['review_id']]
        for key in FIXED:
            if r.get(key)!=before[key]:raise ValueError('Immutable field mismatch: '+r['review_id']+'/'+key)
        if th(r['unchanged_raw_continuation'])!=r['raw_text_sha256']:raise ValueError('Raw text hash mismatch')
        if not r.get('reviewer_id','').strip() or not r.get('reviewer_independence_declaration','').strip():
            raise ValueError('Actual reviewer identity and independence declaration required')
        if r.get('boundary_disposition') not in DECISIONS:raise ValueError('Mandatory boundary decision missing/invalid')
        if r.get('answer_delivered') not in {'YES','PARTIAL','NO','UNCERTAIN'}:raise ValueError('Answer-delivery judgment invalid')
        if not r.get('supporting_boundary_cues','').strip():raise ValueError('Case-specific supporting explanation required')
        disposition=r['boundary_disposition'];text=r.get('accepted_spans_json','').strip()
        spans=json.loads(text) if text else None
        if disposition=='UNRESOLVED':
            if spans is not None:raise ValueError('Unresolved disposition must not invent an accepted span')
            if not r.get('uncertainty','').strip():raise ValueError('Unresolved boundary requires uncertainty reason')
        else:
            if not isinstance(spans,list):raise ValueError('Accepted span list required')
            if disposition=='NO_RECOVERABLE_REPLY' and spans!=[]:raise ValueError('No-reply disposition requires empty list')
            if disposition=='UNIQUE_DEFENSIBLE_SPAN' and len(spans)!=1:raise ValueError('Unique boundary needs one span')
            if disposition=='MULTIPLE_DEFENSIBLE_SPANS' and len(spans)<2:raise ValueError('Multiple boundary needs alternatives')
            for span in spans:
                if not isinstance(span,list) or len(span)!=2 or any(type(x) is not int for x in span):raise ValueError('Invalid character offsets')
                if not 0<=span[0]<span[1]<=len(r['unchanged_raw_continuation']):raise ValueError('Character offsets outside raw text')
            if len({tuple(s) for s in spans})!=len(spans):raise ValueError('Duplicate accepted spans')
        if disposition=='MULTIPLE_DEFENSIBLE_SPANS' and not r.get('alternative_interpretations','').strip():
            raise ValueError('Alternative boundaries require explanations')
        result.append({**r,'validated_spans':spans,'independence_status':'DECLARED_NOT_AUTOMATICALLY_ESTABLISHED',
            'researcher_adoption':'NOT_INFERRED','original_structural_label_changed':False})
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('returned_csv');args=p.parse_args()
    rows=validate_returned(read_rows(args.returned_csv))
    print({'schema_valid_records':len(rows),'automatic_researcher_adoptions':0,'historical_labels_modified':0})

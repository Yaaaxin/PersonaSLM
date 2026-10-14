"""Preserve item-specific AI review observations; no semantic ratings or inference."""
import argparse
import csv
import json
from pathlib import Path
import p1c_design as d

SOURCE=Path('docs/validation/p1c/calibration_v1/measurement_v1/semantic_scoring_view_v1.csv')
# Selected after reading every masked first span. These are transparent review
# notes, not an automatic classifier, human judgments or a fitted algorithm.
CONFLICTS={9,11,12,16,19,27,29,30,31,33,35,37,39,40,42,48,49,53,54,58,65,67,70,71}
SPECIAL={
    4:'The response calls Cobalt a collection desk whereas the requested type is destination room. Assess whether the supported value answers the question despite this attribute wording.',
    6:'The wording "on Thursday, 2042-12-15" may conflate a recurring service-day attribute with the weekday of the query date. Preserve that ambiguity; the ledger supplies the service-day attribute, not a calendar computation.',
    11:'Laurel occurs for Archive colleague 5 in the queried interval; the named speaker route points to Silver. This is a possible entity/attribute substitution, not proof of a history-caused mechanism.',
    27:'Laurel is a colleague collection desk; the question asks for the named speaker destination room via the route. Do not collapse these entities or attributes.',
    30:'The reply supplies Laurel as parcel assignment, while the named speaker route and destination facts require Silver. Identify the selected entity before assigning an error mechanism.',
    33:'Tuesday is supported, but Silver is the colleague desk, not Elian Moss\'s requested desk Maple. Distinguish partial component support from full success.',
    39:'Neither the asserted Silver desk nor Friday service day matches the target interval. Friday is not supported by this ledger; distinguish unsupported content from selection of a dated target fact.',
    42:'The Silver/Friday answer differs from Maple/Tuesday. Friday is absent from the trusted ledger, so a uniform stale-fact explanation is unsupported.'}


def prepare(output):
    output=Path(output)
    if output.exists():raise FileExistsError('Preserve previous analytical suggestions')
    with SOURCE.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    d.require(len(rows)==72 and {r['anonymous_response_id'] for r in rows}=={f'PC{i:03d}' for i in range(1,73)},'Masked inventory differs')
    observations=[]
    for row in rows:
        number=int(row['anonymous_response_id'][2:]);reply=row['raw_first_reply']
        d.require(d.text_hash(reply)==row['first_reply_sha256'],'Original first span differs')
        ids=json.loads(row['reference_fact_ids'])
        quotes=[line for line in row['trusted_evidence'].splitlines() if any(line.startswith('['+i+']') for i in ids)]
        d.require(len(quotes)==len(ids),'Supporting source quotations missing')
        conflict=number in CONFLICTS
        note=(f'The reply asserts an answer that differs from required components {row["required_answer_components"]} at requested date {row["requested_date"]}. Compare the exact claim with the quoted target facts; no final label is assigned here.' if conflict else
              f'The visible answer appears consistent with required components {row["required_answer_components"]} for {row["requested_date"]}. Verify assertion scope, entity/attribute wording and full delivery; matching words alone is insufficient.')
        if number in SPECIAL:note+=' '+SPECIAL[number]
        if 'USER QUESTION:' in reply or 'RECENT CONVERSATION:' in reply:
            note+=' The supplied span also contains a new section heading. Keep the span unchanged; defer its user-facing boundary disposition to separate Stage B review.'
        observations.append({'anonymous_response_id':row['anonymous_response_id'],'anonymous_case_id':row['anonymous_case_id'],
            'first_reply_sha256':row['first_reply_sha256'],'model_span_quotation':reply,'reference_fact_ids':ids,
            'trusted_source_quotations':quotes,'AI_observation':note,'AI_priority':'REVIEW_SPECIFIC_ISSUE' if conflict or number in SPECIAL or 'QUESTION:' in reply or 'CONVERSATION:' in reply else 'STANDARD_REVIEW',
            'annotation_origin':'AI_assisted_reading_of_condition_masked_source','status':'UNCONFIRMED_ANALYTICAL_OBSERVATION',
            'human_decision':'','human_corrections':'','reviewer_id':'','review_timestamp':''})
    d.write_csv(output/'AI_review_observations_UNCONFIRMED_v1.csv',observations)
    d.write_json(output/'provenance_v1.json',{'version':'p1c_AI_review_observations_v1','records':72,
        'source':SOURCE.as_posix(),'source_sha256':d.sha(SOURCE),'source_code_sha256':d.sha(Path(__file__)),
        'output_sha256':d.sha(output/'AI_review_observations_UNCONFIRMED_v1.csv'),'created_utc':d.now(),
        'formal_endpoint_ratings':0,'researcher_confirmations':0,'semantic_effects_computed':False,
        'method':'AI inspected all 72 masked first spans and target references. Code transcribes explicit item-specific review notes; it is not a semantic scoring algorithm.',
        'masking_limit':'Item-note input was condition-masked. The analyst also had access to design and run information; this is not independent blinded annotation.',
        'restriction':'Distribute only as optional assistance after preserving initial Stage A work. Do not import these notes as human labels.'})
    return {'records':72,'formal_endpoint_ratings':0,'human_confirmation':'PENDING','new_generations':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(prepare(parser.parse_args().output),indent=2))

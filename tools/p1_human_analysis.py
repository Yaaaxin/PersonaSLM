"""Register confirmed annotations, then analyze saved outputs offline. No inference."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from personaslm.conditioning import FACTORIAL
from personaslm.human_factorial import VERSION, analyze, material_differences, normalize_confirmed
from personaslm.journal import atomic_json, read_events, utc_now
from personaslm.measurement_audit import HUMAN_FIELDS
from personaslm.response_status import text_hash

PUBLIC = Path('docs/validation/p1')
LOCAL = Path('results/p1_human_analysis/v1')
PROPOSED = PUBLIC/'PersonaSLM_P1_Wave1_96_AI_assisted_structured_review_PENDING_CONFIRMATION.csv'
LEDGER = PUBLIC/'PersonaSLM_P1_Wave1_annotation_provenance_and_confirmation.csv'
MASTER = PUBLIC/'output_human_review_v1.csv'
FINAL = PUBLIC/'output_human_review_researcher_verified_v1.csv'
REGISTER = PUBLIC/'researcher_annotation_registration_v1.json'
SPEC = PUBLIC/'researcher_analysis_specification_v1.json'
MAPPING = Path('results/p1_measurement_audit/v1/admin/output_human_review_mapping_v1.json')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def csv_rows(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream); rows = list(reader)
    if len(reader.fieldnames) != len(set(reader.fieldnames)) or any(None in r or None in r.values() for r in rows):
        raise ValueError('Malformed CSV')
    return rows


def write_csv(path, rows):
    with Path(path).open('x', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def git():
    return {'sha': subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),
            'dirty_status': subprocess.run(['git','status','--short'],capture_output=True,text=True,check=True).stdout}


def verify_saved_prompt(saved):
    """Native P1 records store a prompt object, not a bare string."""
    prompt = saved['prompt']
    if not isinstance(prompt, dict) or not isinstance(prompt.get('text'), str):
        raise ValueError('Malformed saved prompt object')
    if text_hash(prompt['text']) != saved['prompt_sha256']:
        raise ValueError('Prompt hash mismatch')


def pdf_audit(rows, reader_directory):
    sys.path.insert(0, str(reader_directory))
    import pypdf
    candidates = list((PUBLIC/'review_sources').glob('*.pdf'))
    supplied = [p for p in candidates if '已回填' in p.name]
    if len(supplied) != 1:
        raise ValueError('Cannot uniquely identify supplied structured PDF')
    path = supplied[0]; reader = pypdf.PdfReader(path); fields = reader.get_fields() or {}
    checks = []; differences = []
    for row in rows:
        rid = row['anonymous_response_id']; checked = []
        for field in HUMAN_FIELDS:
            if field in ('reviewer_id','review_assistance','prior_access_to_treatments_or_scores','reviewed_utc'):
                continue
            key = rid+'__'+field
            if key not in fields and not row[field]:
                continue  # PDF omits inapplicable choices; CSV blank is preserved in source.
            actual = str(fields.get(key, {}).get('/V', ''))
            if actual != row[field]:
                differences.append({'response_id':rid,'field':field,'pdf':actual,'csv':row[field]})
            checked.append(field)
        checks.append({'response_id':rid,'fields_verified':checked,
                       'marked_done':str(fields.get(rid+'__questionnaire_marked_done',{}).get('/V',''))})
    if differences:
        atomic_json(LOCAL/'pdf_differences.json', differences)
        raise ValueError('PDF/CSV annotation mismatch; see preserved differences')
    return {'source':path.as_posix(),'sha256':sha(path),'reader_version':pypdf.__version__,
            'pages':len(reader.pages),'form_fields':len(fields),'records':checks,'differences':differences,
            'original_uncoded_pdf_located':any(p.name=='PersonaSLM_P1_96条.pdf' for p in candidates),
            'original_pdf_availability_limit':'Original uncoded PDF not found in requested directory or scoped public repository search. Derived PDF verifies narratives/codings but does not independently establish how original radio buttons were filled.',
            'recorded_calendar_date':str(fields.get('common__reviewed_utc',{}).get('/V','')),
            'review_utc':None,'source_assistance_verbatim':str(fields.get('common__review_assistance',{}).get('/V','')),
            'masked_narrative_provenance':'Researcher explicitly confirms condition labels were masked; complete independence from prior experimental knowledge is unknown.'}


def register(reader_directory):
    destinations = [FINAL, REGISTER, PUBLIC/'researcher_annotation_provenance_v1.csv', PUBLIC/'researcher_annotation_normalization_v1.json']
    if any(p.exists() for p in destinations):
        raise FileExistsError('Never overwrite a registered review')
    master, proposed, source_ledger = csv_rows(MASTER), csv_rows(PROPOSED), csv_rows(LEDGER)
    differences = material_differences(master, proposed)
    if differences:
        atomic_json(LOCAL/'material_differences.json', differences)
        raise ValueError('Invalid experimental material; no review imported')
    final, changes, validation = normalize_confirmed(master, proposed, source_ledger)
    pdf = pdf_audit(proposed, reader_directory)
    stamp = utc_now()
    authority = {'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED',
        'final_decision_authority':'researcher','decision_source':'explicit researcher instruction in this conversation',
        'review_method':'condition-masked human narrative review followed by AI-assisted structured coding and explicit researcher confirmation',
        'confirmation_statement':'The previously proposed categorical and numerical annotations are now confirmed by the researcher.',
        'confirmation_utc':None,'registered_utc':stamp,'second_reviewer':None,'inter_annotator_agreement':None,
        'independent_numeric_entry_in_original_pdf':False,'full_prior_knowledge_independence_verified':False}
    # Freeze the final masked file before opening any treatment mapping.
    write_csv(FINAL, final)
    updated = []
    for record in source_ledger:
        updated.append({'anonymous_response_id':record['anonymous_response_id'],
            **{'source_'+k:v for k,v in record.items()},
            'reviewer_id':'Yaxin_ZHENG','review_status':'RESEARCHER_CONFIRMED',
            'researcher_numeric_score_confirmed':'true','final_decision_authority':'researcher',
            'review_method':authority['review_method'],'confirmation_utc':'','registered_utc':stamp,
            'source_ledger_sha256':sha(LEDGER),'final_annotation_sha256':sha(FINAL)})
    write_csv(destinations[2], updated)
    atomic_json(destinations[3], {'version':VERSION,'changes':changes,'scientific_scores_changed':0,
        'mapping':'true/false -> YES/NO; completeness uppercase; categorical title case; blank -> Not Applicable only where frozen applicability=false; assistance=AI-assisted; undocumented prior access=UNCERTAIN.',
        'notes_quotations_and_numeric_ratings_preserved':True,'source_sha256':sha(PROPOSED),'final_sha256':sha(FINAL)})
    registry = {'version':'researcher_verified_annotation_v1','authority':authority,'validation':validation,
        'source_files':{p.as_posix():sha(p) for p in [MASTER,PROPOSED,LEDGER,Path('docs/PersonaSLM_P1_Wave1_annotation_transcription_audit.md')]},
        'final_csv':FINAL.as_posix(),'final_sha256':sha(FINAL),'original_case_count':12,'annotation_count':96,
        'non_annotation_field_differences':differences,'normalization_changes':len(changes),'pdf_audit':pdf,
        'notes_language':'Original researcher notes include Chinese and remain verbatim provenance, not newly introduced dialogue data or silent translations. New reports are English.',
        'source_sha256':{p:sha(p) for p in ['src/personaslm/human_factorial.py','tools/p1_human_analysis.py']},
        'analysis_specification_sha256':sha(SPEC),'git':git(),'mapping_read_before_freeze':False,
        'new_generation_requests':0,'review_times_invented':False,'historical_scores_overwritten':False}
    atomic_json(REGISTER, registry)
    print(json.dumps({'status':'RESEARCHER_CONFIRMED','records':96,'case_count':12,'non_annotation_differences':0,
                      'normalizations':len(changes),'notes_verified_in_derived_pdf':96,'original_uncoded_pdf_located':pdf['original_uncoded_pdf_located']}))


def unblind_and_analyze():
    output = PUBLIC/'researcher_factorial_analysis_v1.json'
    dataset = PUBLIC/'researcher_analysis_dataset_v1.json'
    if output.exists() or dataset.exists():
        raise FileExistsError('Never overwrite analysis results')
    reg = read(REGISTER)
    if reg['authority']['review_status'] != 'RESEARCHER_CONFIRMED' or sha(FINAL) != reg['final_sha256']:
        raise ValueError('Annotations not frozen or changed')
    if sha(SPEC) != reg['analysis_specification_sha256']:
        raise ValueError('Analysis specification changed after annotation freeze')
    source_rows = csv_rows(FINAL)
    for p,h in reg['source_files'].items():
        if sha(p)!=h: raise ValueError('Historical annotation input changed')
    previous = read(PUBLIC/'measurement_audit_v1.json')
    results = PUBLIC/'wave1_results_v1.json'; wavepath = PUBLIC/'wave1_manifest_v1.json'
    if sha(results)!=previous['source_results_sha256'] or sha(wavepath)!=previous['source_manifest_sha256']:
        raise ValueError('Original output or manifest changed')
    wave = read(wavepath)
    if sha('data/synthetic/p1_development_v1.json') != wave['dataset_sha256']:
        raise ValueError('Dataset hash mismatch')
    for key in ('model','backend'):
        config_key = 'model_file' if key=='model' else 'server_file'
        if sha(wave['configuration'][config_key]) != wave[key+'_sha256']:
            raise ValueError('Local inference artifact changed')
    journals=[]
    for journal in previous['journal_audits']:
        folder=Path(journal['directory'])
        inventory={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
        if inventory!=journal['files']: raise ValueError('Historical run changed')
        events=read_events(folder)
        journals.append({'directory':folder.as_posix(),'files':len(inventory),'events':len(events),'chain_valid':True})
    # Only now read the existing curator key. Analyst blindness is not asserted.
    unblind_utc=utc_now(); mapping=read(MAPPING)
    map_rows={r['anonymous_response_id']:r for r in mapping['rows']}
    if len(mapping['rows'])!=96 or len(map_rows)!=96 or set(map_rows)!={r['anonymous_response_id'] for r in source_rows}:
        raise ValueError('Curator mapping ID mismatch')
    native={r['request_id']:r for r in read(results)['rows']}
    if len(native)!=96 or len({r['request_id'] for r in map_rows.values()})!=96:
        raise ValueError('Duplicated or missing treatment association')
    annotations=[]; pairings=defaultdict(set)
    categories={r['anonymous_response_id']:r['coding_category'] for r in csv_rows(LEDGER)}
    master_rows={r['anonymous_response_id']:r for r in csv_rows(MASTER)}
    for row in source_rows:
        rid=row['anonymous_response_id']; key=map_rows[rid]; saved=native[key['request_id']]
        if row['anonymous_case_id']!=key['anonymous_case_id'] or row['raw_sha256']!=key['raw_sha256']:
            raise ValueError('Incorrect anonymous association')
        for name in ('case_id','persona_id','condition','factors'):
            if key[name]!=saved[name]: raise ValueError('Treatment mapping disagrees with saved generation')
        if tuple(key['factors'])!=FACTORIAL[key['condition']]: raise ValueError('Factor routing mismatch')
        if row['raw_full_continuation']!=saved['raw_response'] or row['raw_first_reply']!=saved['parsed_response']:
            raise ValueError('Raw/parsed text differs from original generation')
        if row['raw_sha256']!=text_hash(saved['raw_response']) or row['first_reply_sha256']!=text_hash(saved['parsed_response']):
            raise ValueError('Output hash mismatch')
        if row['structural_status']!=saved['evaluation']['response_completeness']['status']:
            raise ValueError('Frozen structural label changed')
        for axis,value in saved['applicability'].items():
            if row['applicable_'+axis]!=str(value).lower(): raise ValueError('Applicability changed')
        if any(row[f]!=master_rows[rid][f] for f in row if f not in HUMAN_FIELDS):
            raise ValueError('Master material changed during unblinding')
        verify_saved_prompt(saved)
        pairings[row['anonymous_case_id']].add(saved['case_id'])
        annotations.append({'anonymous_response_id':rid,'request_id':saved['request_id'],'case_id':saved['case_id'],
            'persona_id':saved['persona_id'],'condition':saved['condition'],'factors':saved['factors'],'family':saved['family'],
            'annotation':row,'frozen_evaluation':saved['evaluation'],'prompt_sha256':saved['prompt_sha256'],
            'source_narrative_category':categories[rid],'generated_tokens':saved['generated_tokens'],'native_stop_reason':saved['stop_reason']})
    if len(pairings)!=12 or any(len(v)!=1 for v in pairings.values()): raise ValueError('Case mapping is not one-to-one')
    spec=read(SPEC)
    result=analyze(annotations,seed=spec['bootstrap_seed'],replicates=spec['bootstrap_replicates'])
    atomic_json(dataset,{'version':VERSION,'annotation_sha256':sha(FINAL),'registration_sha256':sha(REGISTER),
        'unblinded_utc':unblind_utc,'mapping_sha256':sha(MAPPING),'mapping_distribution':'Analysis-only derived join; original masked CSV unchanged; private shuffle seed not published.',
        'rows':annotations})
    field_counts={f:dict(Counter(r[f] for r in source_rows)) for f in ['human_reply_unit_confirmed','human_semantic_completeness','human_factual_consistency','human_temporal_consistency','human_response_relevance_1_to_5','human_conversational_coherence_1_to_5','structural_status']}
    cross=Counter((r['structural_status'],r['human_semantic_completeness']) for r in source_rows)
    result.update(created_utc=utc_now(),annotation_sha256=sha(FINAL),registration_sha256=sha(REGISTER),
        analysis_dataset_sha256=sha(dataset),analysis_specification_sha256=sha(SPEC),
        source_sha256={p:sha(p) for p in ['src/personaslm/human_factorial.py','tools/p1_human_analysis.py']},
        source_wave_results_sha256=sha(results),dataset_sha256=wave['dataset_sha256'],model_sha256=wave['model_sha256'],backend_sha256=wave['backend_sha256'],
        git=git(),journals=journals,distributions=field_counts,
        structural_semantic_cross_table=[{'structural':s,'semantic':c,'count':n} for (s,c),n in sorted(cross.items())],
        narrative_categories=dict(Counter(categories.values())),MR069=next(r for r in annotations if r['anonymous_response_id']=='MR069'),
        controls_reviewed=0,controls_status='OPEN',new_generations=0,
        limitations=['Single researcher confirmation of assisted numerical coding; no inter-annotator agreement',
            'Condition-masked narrative review per researcher; prior knowledge unknown; original uncoded PDF unavailable locally',
            '12 speaker-case units; family/style/speaker partly confounded; one model/template/budget',
            'Ordinal means and bootstrap intervals are exploratory; no population null, equivalence or significance claim',
            'Factual and temporal ceilings contain no observed discrimination; no control-adjusted outcomes'])
    atomic_json(output,result)
    print(json.dumps({'version':VERSION,'records':96,'distributions':field_counts,
                      'annotation_status':'RESEARCHER_CONFIRMED','new_generations':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['register','analyze'])
    parser.add_argument('--pdf-reader-directory',type=Path,default=LOCAL/'pdf_reader')
    args=parser.parse_args()
    if args.operation=='register': register(args.pdf_reader_directory)
    else: unblind_and_analyze()

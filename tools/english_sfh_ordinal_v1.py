"""Additive, retrospective ordinal intake; mapping access requires a sealed lock."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

import english_sfh_archival_reproduce_v1 as archive
import english_sfh_review_v1 as review
import english_sfh_review_recover_v1 as recovery
import english_sfh_review_delivery_v1 as delivery_bridge

PUBLIC = Path('docs/validation/p1/english_human_ordinal_v1')
PRIVATE = Path('.local/experiments/english_sfh_ordinal_v1')
AMENDMENT = PUBLIC / 'analysis_amendment_v1.json'
DECLARATION = PRIVATE / 'scale_clarification_received_v1.txt'
AMENDMENT_SHA = '04428a566d453a02b6d8d2f2cdd1a369e593e7d0bcaaa5819875601e603a253e'
DECLARATION_SHA = 'f2c5c2432a7e1bd45670699607d0317fc38f52eee8f9c283d795bdbe5f7ec930'
LOCK = PUBLIC / 'ordinal_analysis_lock_v1.json'
LOCKED_ROWS = PRIVATE / 'ordinal_primary_locked_v1.json'
ANALYSIS = PUBLIC / 'ordinal_analysis_v1.json'
JOINED = PRIVATE / 'ordinal_analysis_private_v1.json'
ACCESS = PRIVATE / 'mapping_access_v1.json'
DELIVERY = Path('.local/reviewer-packages/english_sfh_development_v1')
SUBMISSION = DELIVERY / 'WORKING.txt'
RECEIPT = Path('.local/experiments/english_sfh_v1/review/development/package_receipt_v1.json')
MAPPING = RECEIPT.with_name('protected_mapping_v1.json')
UNCERTAINTY = RECEIPT.parent / 'submissions/20261019_received_v1/blank_uncertainty_declaration_v1.json'
HUMAN_DECLARATION = RECEIPT.parent / 'submissions/20261019_received_v1/human_declaration_received_v1.json'
SUBMISSION_SHA = '1c7c5bd5bc1684591df5c1a1c959fce763b10f9de475d7436299ce221a3b1aee'
RECEIPT_SHA = 'e1cf909df2103d6c4d63a3a617984efa875c79509f140854b7050a9958922449'
MAPPING_SHA = '4b5018f61edba8385b16dbad384358acfce639587809b785f0d82d6a4f08f806'
TECHNICAL_SHA = '84468a7ccf42ba9ea8d368ee9800b211c2d97d1422c1ad7fa234b163f3066a53'
REPRODUCTION_SHA = 'ce361877f9c7f47227105c3cb4db75d9575a927258c192bd33e48cddc650cb87'
DOMAINS = ('relevance', 'coherence', 'linguistic_resemblance')
CONDITIONS = tuple('C' + str(i) for i in range(8)) + ('M_STYLE', 'N_STYLE')
MASKS = {'S': 1, 'F': 2, 'H': 4, 'SF': 3, 'SH': 5, 'FH': 6, 'SFH': 7}
CONTROLS = {'correct_minus_mismatched': ('C7', 'M_STYLE'),
            'correct_minus_pooled': ('C7', 'N_STYLE'), 'correct_minus_no_style_at_FH': ('C7', 'C6')}


def require(value, message):
    if not value:
        raise ValueError(message)


def summary(units):
    grouped = defaultdict(list)
    for speaker, value, completions in units:
        grouped[speaker].append(value)
    means = sorted(statistics.fmean(values) for values in grouped.values() if all(v is not None for v in values))
    loo = [statistics.fmean(means[:i] + means[i + 1:]) for i in range(len(means))] if len(means) > 1 else []
    full = [statistics.fmean(u[2][i] for u in units) for i in range(len(units[0][2]))]
    return {'allocated_units': len(units), 'observed_units': sum(u[1] is not None for u in units),
            'complete_speakers': len(means), 'speaker_values_sorted': means,
            'positive': sum(v > 0 for v in means), 'zero': means.count(0), 'negative': sum(v < 0 for v in means),
            'mean_complete_speakers': statistics.fmean(means) if means else None,
            'leave_one_speaker_out_mean_range': [min(loo), max(loo)] if loo else None,
            'full_design_completion_values': full, 'full_design_bounds': [min(full), max(full)]}


def threshold_units(cases, domain, threshold, coefficients, scenarios):
    units = []
    for (speaker, _), cells in sorted(cases.items()):
        for condition, coefficient in coefficients.items():
            value = cells[condition]['ratings'][domain]
            result = coefficient * int(value >= threshold) if value is not None else None
            units.append((speaker, result, [coefficient * int((category if value is None else value) >= threshold)
                                           for category in scenarios]))
    return summary(units)


def paired(cases, domain, pairs, scenarios):
    metrics = {name: [] for name in ('win', 'tie', 'loss', 'net')}
    joint = {quality + '_' + speed: [] for quality in ('win', 'tie', 'loss') for speed in ('faster', 'equal', 'slower')}
    for (speaker, _), cells in sorted(cases.items()):
        for high, low in pairs:
            a, b = cells[high]['ratings'][domain], cells[low]['ratings'][domain]
            speed = ('faster' if cells[high]['latency_seconds'] < cells[low]['latency_seconds'] else
                     'slower' if cells[high]['latency_seconds'] > cells[low]['latency_seconds'] else 'equal')
            possibilities = [(category if a is None else a, category if b is None else b) for category in scenarios]
            observed = a is not None and b is not None
            for name, units in metrics.items():
                values = [int(x > y) if name == 'win' else int(x == y) if name == 'tie' else
                          int(x < y) if name == 'loss' else int(x > y) - int(x < y) for x, y in possibilities]
                units.append((speaker, values[0] if observed else None, values))
            for name, units in joint.items():
                quality, required_speed = name.split('_')
                values = [int(speed == required_speed and (x > y if quality == 'win' else x == y if quality == 'tie' else x < y))
                          for x, y in possibilities]
                units.append((speaker, values[0] if observed else None, values))
    return {**{name: summary(values) for name, values in metrics.items()},
            'quality_latency': {name: summary(values) for name, values in joint.items()}}


def compute(rows):
    """Float/stdlib implementation, independent of the Fraction reproduction engine."""
    cases, speakers = defaultdict(dict), defaultdict(set)
    for row in rows:
        require(set(row['ratings']) == set(DOMAINS), 'Exactly three primary domains required')
        values = list(row['ratings'].values())
        require(all(v is None for v in values) or all(type(v) is int and 0 <= v <= 5 for v in values),
                'Original integer0–5 values or a wholly unavailable record required')
        require(type(row['latency_seconds']) in (int, float) and math.isfinite(row['latency_seconds'])
                and row['latency_seconds'] >= 0, 'Finite nonnegative technical latency required')
        key = row['speaker_id'], row['case_id']
        require(row['condition'] in CONDITIONS and row['condition'] not in cases[key], 'Duplicate or unknown condition')
        cases[key][row['condition']] = row
        speakers[key[0]].add(key[1])
    require(len(rows) == 100 and len(speakers) == 5 and all(len(c) == 2 for c in speakers.values())
            and all(set(c) == set(CONDITIONS) for c in cases.values()), 'Frozen five-speaker two-context ten-condition grid required')
    missing = sum(row['ratings'][DOMAINS[0]] is None for row in rows)
    require(missing <= 1, 'At most one wholly unavailable record for the registered completion sensitivity')
    scenarios = list(range(6)) if missing else [None]
    result = {'schema': 'english_sfh_ordinal_arithmetic_v1', 'speakers': 5, 'contexts': 10, 'responses': 100, 'domains': {}}
    for domain in DOMAINS:
        distribution = {}
        for condition in CONDITIONS:
            values = [row['ratings'][domain] for row in rows if row['condition'] == condition]
            observed = sorted(v for v in values if v is not None)
            central = ([observed[len(observed)//2]] if len(observed) % 2 else
                       observed[len(observed)//2-1:len(observed)//2+1]) if observed else None
            distribution[condition] = {'counts': [values.count(k) for k in range(6)],
                                       'observed': len(observed), 'missing': values.count(None), 'central_categories': central}
        effects = {}
        for name, mask in MASKS.items():
            coefficients = {'C' + str(i): 2 * math.prod(1 if i & bit else -1 for bit in (1, 2, 4) if mask & bit)
                            for i in range(8)}
            effects[name] = {str(k): threshold_units(cases, domain, k, coefficients, scenarios) for k in range(1, 6)}
        mains = {name: paired(cases, domain, [('C' + str(i | bit), 'C' + str(i)) for i in range(8) if not i & bit], scenarios)
                 for name, bit in list(MASKS.items())[:3]}
        controls = {name: {'thresholds': {str(k): threshold_units(cases, domain, k, {high: 2, low: -2}, scenarios) for k in range(1, 6)},
                           'paired': paired(cases, domain, [(high, low)], scenarios)} for name, (high, low) in CONTROLS.items()}
        result['domains'][domain] = {'completion_category_scenarios': scenarios, 'condition_distributions': distribution, 'threshold_factorial': effects,
                                     'paired_main': mains, 'style_controls': controls}
    return result


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(path, expected):
    require(sha(path) == expected, 'Hash-bound input changed: ' + Path(path).name)
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sources():
    root = Path.cwd().resolve()
    paths = {Path(__file__).resolve(), review.RUBRIC.resolve()}
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path:
            path = Path(path).resolve()
            if path.is_relative_to(root) and path.suffix == '.py' and path.parts[len(root.parts)] in ('tools', 'src'):
                paths.add(path)
    for relative in ('tools/english_sfh_ordinal_independent_v1.py', 'tests/test_english_sfh_ordinal_v1.py',
                     'tests/test_english_sfh_ordinal_independent_v1.py'):
        paths.add((root / relative).resolve())
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths)}


def intake(package, raw, uncertainty):
    require(hashlib.sha256(raw).hexdigest() == SUBMISSION_SHA, 'Original human submission changed')
    assigned = {r['review_id'] for r in package['rows']}
    submitted = recovery.parse_rows(raw, assigned)
    require(len(package['rows']) == 100 and len(submitted) == 99, 'Frozen100 allocation and99 actual submitted records required')
    require(uncertainty.get('schema') == 'english_sfh_blank_uncertainty_declaration_v1' and
            uncertainty.get('received_submission_sha256') == SUBMISSION_SHA and
            uncertainty.get('blank_entries_mean_uncertainty') is True and uncertainty.get('author') == 'PRINCIPAL_RESEARCHER',
            'Actual submission-bound uncertainty declaration required')
    by_id = {row['review_id']: row for row in submitted}
    restored, primary = [], []
    for record in package['rows']:
        human = by_id.get(record['review_id'])
        ratings = dict.fromkeys(DOMAINS)
        if human:
            require(all(human[name] in tuple(str(i) for i in range(6)) for name in DOMAINS), 'Primary rating outside exact integer0–5 scale')
            ratings = {name: int(human[name]) for name in DOMAINS}
        primary.append({'review_id': record['review_id'], 'ratings': ratings,
                        'primary_status': 'HUMAN_SUBMITTED' if human else 'UNAVAILABLE'})
        restored.append({**review.csv_display(record), **{name: human[name] if human else '' for name in review.EDITABLE}})
    old = review.validate_submission(package, review.encode_csv(restored, review.FIELDS), final=False)
    require(not any('Immutable' in error['message'] or error['code'] in ('CSV_INVALID', 'FIXED_RECORD_SET_REQUIRED')
                    for error in old['errors']), 'Immutable package alignment changed')
    return primary, {'assigned': 100, 'primary_observed': 99, 'primary_unavailable': 1,
                     'original_rubric_pass': False, 'original_validator_errors': dict(Counter(e['message'] for e in old['errors'])),
                     'secondary_applicability_claims_confidence': 'PRESERVED_NOT_ANALYZED_NOT_REINTERPRETED'}


def lock(amendment, amendment_sha256, declaration, declaration_sha256):
    require(not LOCK.exists() and not LOCKED_ROWS.exists(), 'Existing ordinal lock; no overwrite')
    amendment, declaration = Path(amendment), review.private_path(declaration)
    protocol = checked(amendment, amendment_sha256)
    require(declaration_sha256 == DECLARATION_SHA and sha(declaration) == DECLARATION_SHA,
            'Actual verbatim researcher scale declaration changed')
    validate_protocol(protocol, amendment_sha256)
    for module, digest in recovery.FROZEN_SOURCES.items():
        require(sha(sys.modules[module].__file__) == digest, 'Frozen review helper changed')
    require(sha(review.RUBRIC) == recovery.RUBRIC_SHA, 'Original frozen rubric changed')
    checked(RECEIPT, RECEIPT_SHA)
    package = review.load_package(DELIVERY, RECEIPT)
    uncertainty = json.loads(UNCERTAINTY.read_text(encoding='utf-8'))
    primary, qc = intake(package, SUBMISSION.read_bytes(), uncertainty)
    private = {'schema': 'english_sfh_primary_ordinal_locked_v1', 'submission_sha256': SUBMISSION_SHA,
               'rows': primary, 'all_other_raw_human_values_preserved_at_source': True}
    bindings = {str(amendment): amendment_sha256, str(declaration): declaration_sha256,
                str(SUBMISSION): SUBMISSION_SHA, str(RECEIPT): RECEIPT_SHA,
                str(UNCERTAINTY): sha(UNCERTAINTY), str(HUMAN_DECLARATION): sha(HUMAN_DECLARATION),
                str(archive.ANALYSIS): TECHNICAL_SHA, str(archive.REPRODUCTION): REPRODUCTION_SHA,
                str(archive.resume.PARENT_MANIFEST): archive.resume.PARENT_SHA}
    for path, expected in bindings.items():
        require(sha(path) == expected, 'Input changed before ordinal lock: ' + Path(path).name)
    human = json.loads(HUMAN_DECLARATION.read_text(encoding='utf-8'))
    require(human.get('submission_sha256') == SUBMISSION_SHA and
            human.get('human_authorship') == 'AFFIRMED_BY_PRINCIPAL_RESEARCHER' and
            human.get('blinded_review') == 'AFFIRMED_BY_PRINCIPAL_RESEARCHER', 'Actual human declaration binding changed')
    report = {'schema': 'english_sfh_ordinal_analysis_lock_v1', 'created_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'AMENDED_PRIMARY_ORDINAL_LOCKED_NOT_ORIGINAL_RUBRIC_PASS', 'bindings': bindings,
              'source_hashes': sources(), 'qc': qc, 'protected_mapping_opened': False,
              'condition_effects_calculated': False, 'human_labels_created_or_changed': 0,
              'provenance': {'human_authorship': 'AFFIRMED_BY_PRINCIPAL_RESEARCHER',
                'blinded_review': 'AFFIRMED_BY_PRINCIPAL_RESEARCHER', 'independent_of_project': False,
                'double_blind_review_established': False, 'absence_of_prior_exposure_verified': False,
                'inter_rater_reliability': False, 'detailed_exposure_competence_aids_and_annotation_dates': 'UNKNOWN_NOT_INVENTED'},
              'scale': 'Original0–5 ordered categories, zero valid, higher better; no intermediate anchors/equal interval assumption.',
              'analysis_timing': 'RETROSPECTIVE_AMENDMENT_AFTER_RATINGS_BEFORE_CONDITION_JOIN',
              'new_generations': 0, 'new_inference_seconds': 0}
    review.prior.write_exclusive(LOCKED_ROWS, review.json_bytes(private))
    report['private_locked_rows_sha256'] = sha(LOCKED_ROWS)
    review.prior.write_exclusive(LOCK, review.json_bytes(report))
    return {'status': report['status'], 'lock_sha256': sha(LOCK), 'primary_observed': 99, 'primary_unavailable': 1}


def validate_protocol(protocol, expected_hash):
    require(expected_hash == AMENDMENT_SHA and
            protocol.get('schema') == 'personaslm_english_primary_ordinal_analysis_amendment_v1' and
            protocol['inputs']['received_submission_sha256'] == SUBMISSION_SHA and
            protocol['scale']['actual_categories'] == list(range(6)) and protocol['scale']['equal_intervals'] is False,
            'Exact frozen retrospective ordinal amendment required')


def verify_lock(expected_hash):
    doc = checked(LOCK, expected_hash)
    require(doc.get('schema') == 'english_sfh_ordinal_analysis_lock_v1' and
            doc.get('protected_mapping_opened') is False and doc.get('condition_effects_calculated') is False,
            'Require pre-mapping ordinal lock')
    for path, expected in {**doc['bindings'], **doc['source_hashes']}.items():
        require(sha(path) == expected, 'Locked source/input changed: ' + Path(path).name)
    rows = checked(LOCKED_ROWS, doc['private_locked_rows_sha256'])['rows']
    package = review.load_package(DELIVERY, RECEIPT)
    fresh, qc = intake(package, SUBMISSION.read_bytes(), json.loads(UNCERTAINTY.read_text(encoding='utf-8')))
    require(fresh == rows and qc == doc['qc'], 'Locked primary values differ from untouched original')
    return doc, rows, package


def joined_rows(package, locked, mapping, plan, technical, raw):
    require(mapping['sealed_source_sha256'] == TECHNICAL_SHA and len(mapping['rows']) == 100, 'Protected mapping source binding')
    assignments = {r['request_id']: r for r in plan['requests']}
    metrics = {r['request_id']: r for r in technical['rows']}
    records = {r['review_id']: r for r in package['rows']}
    primary = {r['review_id']: r for r in locked}
    links = {r['review_id']: r for r in mapping['rows']}
    dossiers = {key: delivery_bridge.dossier(case) for key, case in delivery_bridge.case_lookup(plan).items()}
    require(len(assignments) == len(metrics) == len(records) == len(primary) == len(links) == len(raw) == 100
            and set(links) == set(records) == set(primary) and
            {r['request_id'] for r in links.values()} == set(assignments) == set(metrics) == set(raw), 'Exact one-to-one100-record join required')
    result = []
    for review_id, link in links.items():
        record, request = records[review_id], assignments[link['request_id']]
        require(link['display_sha256'] == hashlib.sha256(review.json_bytes(record)).hexdigest()
                and record['response'] == raw[link['request_id']]['response']['content']
                and link['case_id'] == request['case_id'] and record['dossier'] == dossiers[request['case_id']]
                and record['outcome_status'] == 'GENERATED', 'Mapping display/response/case/dossier mismatch')
        metric = metrics[link['request_id']]
        require(all(metric[k] == request[k] for k in ('speaker_id', 'case_id', 'condition')) and
                metric['measurements']['latency_seconds'] == raw[link['request_id']]['latency_seconds'], 'Raw technical row mismatch')
        result.append({**{k: request[k] for k in ('speaker_id', 'case_id', 'condition')},
                       'ratings': primary[review_id]['ratings'], 'latency_seconds': metric['measurements']['latency_seconds']})
    return result


def analyze(lock_sha256, authorize_mapping=False, verify=False):
    require(authorize_mapping is True, 'Explicit root-authorized mapping access required after lock')
    doc, primary, package = verify_lock(lock_sha256)
    require(verify or (not ANALYSIS.exists() and not JOINED.exists() and not ACCESS.exists()), 'Ordinal analysis/access attempt exists; no overwrite')
    reproduced = archive.reproduce(TECHNICAL_SHA, REPRODUCTION_SHA)
    report = checked(archive.ANALYSIS, TECHNICAL_SHA)
    prior = checked(archive.REPRODUCTION, REPRODUCTION_SHA)
    plan = checked(archive.resume.PARENT_MANIFEST, archive.resume.PARENT_SHA)
    technical = checked(archive.PRIVATE / 'development_combined_analysis_private_v1.json', prior['private_file_sha256'])
    raw = {}
    for receipt in report['run_receipts']:
        events = archive.independent.read_events(Path(receipt['run_directory']))
        require(events[-1]['event_hash'] == receipt['terminal_event_sha256'], 'Sealed raw tail changed')
        for event in events:
            if event['kind'] == 'english_sfh_raw':
                item = event['data']
                require(item['request_id'] not in raw, 'Duplicate raw response')
                raw[item['request_id']] = item
    if verify:
        saved_report = json.loads(ANALYSIS.read_text(encoding='utf-8'))
        access = checked(ACCESS, saved_report['mapping_access_receipt_sha256'])
        require(access['lock_sha256'] == lock_sha256 and access['mapping_expected_sha256'] == MAPPING_SHA,
                'Original mapping access receipt binding changed')
    else:
        access = {'schema': 'english_sfh_ordinal_mapping_access_v1', 'status': 'AUTHORIZED_ACCESS_ATTEMPT_STARTED',
                  'first_access_attempt_utc': datetime.now(timezone.utc).isoformat(),
                  'lock_sha256': lock_sha256, 'mapping_expected_sha256': MAPPING_SHA,
                  'limits': 'Written before the first protected-map read; successful analysis separately verifies the join.'}
        review.prior.write_exclusive(ACCESS, review.json_bytes(access))
    mapping = checked(MAPPING, MAPPING_SHA)
    require(package['receipt']['protected_mapping_sha256'] == MAPPING_SHA, 'Package/map hash conflict')
    rows = joined_rows(package, primary, mapping, plan, technical, raw)
    estimates = compute(rows)
    import english_sfh_ordinal_independent_v1 as independent
    require(Path(independent.__file__).resolve() == (Path.cwd() / 'tools/english_sfh_ordinal_independent_v1.py').resolve()
            and sha(independent.__file__) == doc['source_hashes']['tools/english_sfh_ordinal_independent_v1.py'], 'Independent source changed')
    archive.independent.compare(estimates, independent.compute(rows), 'Independent ordinal arithmetic')
    private = {'schema': 'english_sfh_ordinal_joined_v1', 'lock_sha256': lock_sha256, 'rows': rows}
    result = {'schema': 'english_sfh_ordinal_analysis_v1', 'status': 'PASS_INDEPENDENT_ARITHMETIC_NOT_INDEPENDENT_HUMAN_VALIDATION',
              'lock_sha256': lock_sha256, 'protected_mapping_sha256': MAPPING_SHA, 'estimates': estimates,
              'mapping_access_receipt_sha256': sha(ACCESS),
              'coverage': doc['qc'], 'provenance': doc['provenance'], 'original_values_rescaled': False,
              'secondary_fields_analyzed': False, 'human_labels_created_or_changed': 0, 'new_generations': 0,
              'new_inference_seconds': 0, 'cumulative_generations': reproduced['cumulative_generations'],
              'cumulative_inference_seconds': reproduced['cumulative_inference_seconds'],
              'analysis_timing': doc['analysis_timing'], 'source_hashes': doc['source_hashes'],
              'limits': 'Retrospective exploratory PI-perceived relevance, coherence and linguistic resemblance, not independent review or validated behavioral fidelity. Unanchored ordinal categories, no equal-interval means, no calibrated significance or confidence intervals. Speaker/meeting/topic dependence persists. LOO is influence only. Missing bounds are per-estimand logical bounds, not simultaneous confidence intervals. Exact latency signs do not establish a practically important speed difference or causal mediation. Secondary applicability, claims and confidence are unchanged and unanalyzed. Public clone-only reproduction PARTIAL; authentic journals and blinded package remain private.'}
    if verify:
        stored_private = checked(JOINED, json.loads(ANALYSIS.read_text())['private_joined_sha256'])
        require({k: v for k, v in stored_private.items() if k != 'first_mapping_access_utc'} == private, 'Private ordinal reproduction differs')
        saved = json.loads(ANALYSIS.read_text(encoding='utf-8'))
        archive.independent.compare({k: v for k, v in saved.items() if k not in ('created_utc', 'private_joined_sha256')}, result, 'Saved ordinal analysis')
    else:
        review.prior.write_exclusive(JOINED, review.json_bytes(dict(private, first_mapping_access_utc=access['first_access_attempt_utc'])))
        review.prior.write_exclusive(ANALYSIS, review.json_bytes(dict(result, created_utc=datetime.now(timezone.utc).isoformat(), private_joined_sha256=sha(JOINED))))
    return {'status': result['status'], 'analysis_sha256': sha(ANALYSIS), 'new_generations': 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--lock', action='store_true')
    mode.add_argument('--analyze', action='store_true')
    mode.add_argument('--verify', action='store_true')
    for name in ('amendment', 'amendment-sha256', 'scale-declaration', 'scale-declaration-sha256', 'lock-sha256'):
        parser.add_argument('--' + name)
    parser.set_defaults(amendment=str(AMENDMENT), scale_declaration=str(DECLARATION))
    parser.add_argument('--authorize-mapping', action='store_true')
    args = parser.parse_args(argv)
    if args.lock:
        require(all((args.amendment, args.amendment_sha256, args.scale_declaration, args.scale_declaration_sha256)) and not args.authorize_mapping,
                'Lock requires exact amendment/declaration bindings and forbids mapping authorization')
        result = lock(args.amendment, args.amendment_sha256, args.scale_declaration, args.scale_declaration_sha256)
    else:
        require(args.lock_sha256, 'Externally verified lock SHA required')
        result = analyze(args.lock_sha256, args.authorize_mapping, args.verify)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

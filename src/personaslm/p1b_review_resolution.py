"""Resolve CSV-only P1b audit questions without changing stimuli or human labels."""
from collections import Counter
from copy import deepcopy
import json
import re

from .inference import LlamaClient, validate_token_ids
from .p1b import prompt, hash_text, canonical_hash
from .p1b_readiness import audit, requests

VERSION = 'p1b_review_resolution_v1'


class TokenizationOnlyClient(LlamaClient):
    """Fail closed before HTTP if any caller attempts generation."""
    def request(self, route, payload=None):
        if route not in ('/health', '/props', '/tokenize'):
            raise ValueError('This preflight permits tokenization only; generation is forbidden')
        return super().request(route, payload)

    def complete(self, *args, **kwargs):
        raise ValueError('Generation is forbidden in the scientific-review task')


def indexed(rows, expected_ids):
    if len(rows) != len(expected_ids) or len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Missing or duplicate case IDs')
    result = {r['case_id']: r for r in rows}
    if set(result) != set(expected_ids):
        raise ValueError('Unknown or missing case IDs')
    return result


def compare_review_sources(master, suggested, independent):
    """Read every field; preserve the original 41 fields and all AI suggestions."""
    if len(master) != 24 or len(master[0]) != 41:
        raise ValueError('Original 24-record, 41-column review master required')
    ids = {r['case_id'] for r in master}
    old = indexed(master, ids); proposed = indexed(suggested, ids); external = indexed(independent, ids)
    checked = []
    for cid, source in old.items():
        row, separate = proposed[cid], external[cid]
        if not set(source) <= set(row):
            raise ValueError('Suggestion file omits original fields')
        differences = [k for k, v in source.items() if row[k] != v]
        if differences:
            raise ValueError(f'Original review fields changed for {cid}: {differences}')
        if separate['source_review_version'] != source['review_version'] or separate['persona_id'] != source['persona_id']:
            raise ValueError('Independent analysis source mismatch')
        if json.loads(separate['reference_answer']) != json.loads(source['expected_answer']):
            raise ValueError('Independent analysis reference differs')
        shared = set(row) & set(separate)
        if any(row[k] != separate[k] for k in shared):
            raise ValueError('Supplied analysis versions disagree')
        quotations = separate['ai_reference_quotes'].split(' | ')
        if any(q not in source['trusted_evidence'] for q in quotations):
            raise ValueError('Analysis quotation not present in source')
        human = {k: v for k, v in source.items() if k.startswith('check_') or k in (
            'researcher_decision', 'reviewer_id', 'review_method', 'reviewed_utc', 'evidence_quotations', 'reviewer_notes')}
        checked.append({'case_id': cid, 'original_fields_equal': 41, 'human_fields_verbatim': human,
                        'ai_proposed_status': separate['ai_proposed_status'],
                        'source_row_sha256': canonical_hash(source), 'ai_row_sha256': canonical_hash(separate)})
    return {'version': VERSION, 'source_rows': 24, 'original_fields_compared': 24*41,
            'original_fields_changed': 0, 'ai_status_counts': dict(Counter(r['ai_proposed_status'] for r in independent)),
            'human_decisions_present': sum(bool(r['researcher_decision']) for r in master),
            'review_provenance': 'Supplied AI analysis; researcher confirmation pending. Not a blind human review.', 'cases': checked}


def recent_turns(text):
    delimiter = '\n\nRECENT CONVERSATION:\n'
    if text.count(delimiter) != 1:
        raise ValueError('Expected exactly one recent-conversation section')
    offset = text.index(delimiter) + len(delimiter)
    suffix = text[offset:]
    matches = list(re.finditer(r'(?m)^(User|Assistant):', suffix))
    if not matches or suffix[:matches[0].start()].strip():
        raise ValueError('Unlabelled conversation prefix')
    result = []
    for i, match in enumerate(matches):
        end = matches[i+1].start() if i+1 < len(matches) else len(suffix)
        result.append({'role': match[1], 'start': offset+match.start(), 'end': offset+end,
                       'content': suffix[match.end():end].strip()})
    if len(result) < 2 or result[-1]['role'] != 'Assistant' or result[-1]['content']:
        raise ValueError('Missing final empty Assistant reply boundary')
    if any(not r['content'] for r in result[:-1]):
        raise ValueError('Unexpected empty preceding turn')
    return result


def inspect_prompts(dataset, manifest):
    validation = audit(dataset)
    if manifest['requests'] != requests(dataset):
        raise ValueError('Frozen request/order reconstruction differs')
    by_id = {c['case_id']: c for c in dataset['cases']}
    rows = []
    for r in manifest['requests']:
        c = by_id[r['case_id']]; text = r['prompt']
        anchor = 'Evaluation reference: ' + c['evaluation_date'] + '.'
        if text != prompt(c, r['condition']) or hash_text(text) != r['prompt_sha256']:
            raise ValueError('Prompt bytes/hash changed')
        if text.splitlines()[1] != anchor or text.count(anchor) != 1 or text.index(anchor) >= text.index('TRUSTED EVIDENCE:'):
            raise ValueError('Missing, conflicting or misplaced fictional reference date')
        turns = recent_turns(text)
        if turns[-2] != {**turns[-2], 'role': 'User', 'content': c['question']}:
            raise ValueError('Current question is not the final User message')
        if len(turns) != len(c['context']) + 2:
            raise ValueError('Unexpected role delimiter or merged context')
        for turn, original in zip(turns, c['context']):
            if turn['role'] + ': ' + turn['content'] != original:
                raise ValueError('Fixed context role/text changed')
        adjacent = [i for i in range(1, len(turns)) if turns[i]['role'] == turns[i-1]['role']]
        if adjacent and not (c['case_id'] == 'p1b_H_L3' and adjacent == [3]):
            raise ValueError('Unexpected same-role adjacency')
        rows.append({'request_id': r['request_id'], 'case_id': c['case_id'], 'condition': r['condition'],
                     'prompt_sha256': r['prompt_sha256'], 'reference_date_visible': True,
                     'reference_date_quote': anchor, 'reference_character_offset': text.index(anchor),
                     'reference_clock_scope': 'Fictional evaluation date; not the host clock',
                     'question_has_explicit_date': bool(re.search(r'\d{4}-\d{2}-\d{2}', c['question'])),
                     'recent_turns': turns, 'same_role_adjacency': adjacent,
                     'boundary_status': 'EXPLICIT_SAME_USER_FOLLOWUP' if adjacent else 'EXPLICIT_ALTERNATING_TURNS',
                     'model_boundary_behavior': 'UNTESTED', 'shared_inputs_verified': True})
    return {'version': VERSION, 'status': 'PASS', 'cases': len(by_id), 'prompts': len(rows),
            'visible_reference_dates': sum(r['reference_date_visible'] for r in rows),
            'undated_question_cases': len({r['case_id'] for r in rows if not r['question_has_explicit_date']}),
            'same_user_followup_prompts': sum(bool(r['same_role_adjacency']) for r in rows),
            'dataset_modified': False, 'case_construction_validation': validation['status'], 'requests': rows}


def context_necessity_cases(dataset):
    """Enumerate possible parcel answers without using the focus instruction.

    This is a source-ledger ambiguity test, not a model context-ablation trial.
    """
    results = []
    for c in dataset['cases']:
        if c['family'] != 'H':
            continue
        at = '2027-04-10' if c['case_id'] == 'p1b_H_L3' else c['evaluation_date']
        facts = c['facts']
        def values(subject, relation):
            return [f['value'] for f in facts if f['subject'] == subject and f['relation'] == relation
                    and f['valid_from'] <= at <= (f['valid_until'] or '9999-12-31')]
        parcels = sorted({f['subject'] for f in facts if f['subject'].startswith('Parcel ')})
        answers = {}
        for parcel in parcels:
            desks = values(parcel, 'delivery_desk')
            for recipient in values(parcel, 'recipient'):
                desks += values(recipient, 'delivery_desk')
            if len(desks) != 1:
                raise ValueError('Ambiguous parcel route in trusted evidence')
            answers[parcel] = desks[0]
        results.append({'case_id': c['case_id'], 'proposition_date': at, 'possible_parcel_answers_without_focus': answers,
                        'distinct_possible_answers': len(set(answers.values())),
                        'context_necessity_supported_by_source': len(set(answers.values())) > 1,
                        'empirical_context_use': 'UNTESTED', 'model_requests': 0})
    return results


def tokenized_requests(plan, tokenize, journal_write):
    """Consume the exact frozen strings once; never render, shorten or generate."""
    out = []
    for r in plan:
        if hash_text(r['prompt']) != r['prompt_sha256']:
            raise ValueError('Refuse altered prompt')
        ids = validate_token_ids(tokenize(r['prompt']), allow_empty=False)
        fit = len(ids)+96 <= 4096
        result = {**deepcopy(r), 'input_token_ids': ids, 'input_token_count': len(ids),
                  'token_ids_sha256': canonical_hash(ids), 'tokenizer_preflight': 'PASS',
                  'context_fit': 'PASS' if fit else 'FAILED', 'remaining_context_after_output_budget': 4096-len(ids)-96}
        journal_write('p1b_prompt_tokenized', result)
        if not fit:
            raise ValueError('Actual input tokens plus fixed output budget exceed context; no truncation permitted')
        out.append(result)
    return out

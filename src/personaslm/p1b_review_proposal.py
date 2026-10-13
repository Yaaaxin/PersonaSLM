"""Case-specific AI review proposals; never populate a human field implicitly."""
from datetime import datetime
import json

from .p1b_readiness import CHECKS, validate_reviews

VERSION = 'p1b_stimulus_AI_proposal_v1'
CONFIRM = 'CONFIRM_ALL_PROPOSED_JUDGMENTS'

# Written after inspecting all English questions, ledgers and dialogue contexts.
# These explanations, not the automated audit status, justify the proposed labels.
# The reviewer may disagree; none is an empirical difficulty or human judgment.
NOTES = {
 'A_L1': ('The archive box has one storage-room record: Juniper Room 1.',
          'January 1 through ongoing includes the visible April 15 reference.',
          'Direct retrieval baseline; the only evidence record supplies the answer.'),
 'A_L2': ('The archive box maps to Juniper Room 2; the Willow Room 1 record belongs to a supply box.',
          'Both rooms are currently valid for different boxes, not conflicting values for one box.',
          'One same-relation distractor increases selection demands without adding a reasoning hop; target remains first.'),
 'A_L3': ('The archive box maps to Juniper Room 3; two separately named supply boxes map to Willow rooms.',
          'All three intervals include April 15; object identity, not recency, selects the archive record.',
          'Two distractors and a first-position answer remain an easy retrieval anchor, not demonstrated greater difficulty.'),
 'B_L1': ('Dara belongs to Bookbinding Group 4 and is its materials coordinator; both requested attributes are supplied.',
          'The workshop and role are ongoing from January 1, before the April 15 reference.',
          'Two answer components increase response burden; role wording repeats across B and factual support is separate from completeness.'),
 'B_L2': ('Emery joins Bookbinding Group 5, has the materials coordinator role, and that group meets at Cedar Hall 5.',
          'The person attributes and group-to-place relation are all valid at April 15.',
          'The v2 question explicitly attaches meeting place to workshop; three answer slots do not by themselves prove harder reasoning.'),
 'B_L3': ('Finley joins Bookbinding Group 6 as materials coordinator; the group meets at Cedar Hall 6, whose entrance is east.',
          'All four links are ongoing at April 15; no time-dependent change is requested.',
          'The v2 question explicitly links entrance to the meeting place. Four components may interact with the 96-token budget.'),
 'C_L1': ('Gale uses Birch Counter on April 5; Maple ended March 31 and Cedar starts April 10.',
          'April 5 lies inside the inclusive April 1–9 Birch interval, despite the global April 15 reference.',
          'A dated lookup baseline; explicit dates may make interval selection straightforward.'),
 'C_L2': ('Hollis uses Cedar Counter on April 10; Birch ends on April 9.',
          'The inclusive start date makes Cedar valid on April 10; there is no overlap with Birch.',
          'Boundary selection tests an inclusive start date, not necessarily a difficult reasoning task.'),
 'C_L3': ('Indigo uses Cedar on April 10 and Birch on the preceding day, April 9.',
          'April 9 and April 10 fall in adjacent non-overlapping inclusive intervals.',
          'Two date-specific components test change attribution; output burden also increases and no empirical level ranking is claimed.'),
 'D_L1': ('Jules is assigned Crate 40, and Crate 40 is stored in Locker 60.',
          'Both assignment and storage relation are ongoing on April 15.',
          'Two valid links support Locker 60, but it is the only locker: a correct answer cannot certify traversal.'),
 'D_L2': ('Kit is assigned Crate 41, stored in Locker 61, which is in Fern Room 11.',
          'Assignment, storage and room relations share a valid April 15 interval.',
          'The unique room is a shortcut; the source chain is valid but model use of each link is untested.'),
 'D_L3': ('Linden is assigned Crate 42, stored in Locker 62, in Fern Room 12, in West Annex 12.',
          'All four relations are ongoing at April 15.',
          'The unique building can bypass intermediate links. Retain as calibration, not proof of four-step reasoning.'),
 'E_L1': ('Briar lives in Mereford 2 in 2027; Alderwick 2 was the genuine 2026 residence.',
          'The question asks April 15, 2027; the November 15, 2026 dialogue falls inside the old residence interval.',
          'Current-state selection with relevant past residence; relevance and temporal information are bundled, not isolated.'),
 'E_L2': ('Cleo currently lives in Mereford 3, served by Heron Hub 3; Plover Hub 3 serves the old city.',
          'The current city and both city-to-hub links are valid in 2027; the old residence ended in 2026.',
          'A genuine old-city branch distracts from the current branch; history relevance remains confounded with family E.'),
 'E_L3': ('Dara currently lives in Mereford 4; Heron Hub 4 serves it and opens Tuesday. Plover Hub 4 belongs to the old-city branch.',
          'Use residence on April 15 to select the hub, then its recorded opening weekday; the weekday of April 15 is not the answer rule.',
          'The v2 Tuesday source/key correction removes the earlier calendar coincidence; it does not establish greater discrimination.'),
 'F_L1': ('The question names Morgan North with the exact N identifier, whose shelf is Amber; South has a distinct identifier and Violet Shelf.',
          'Both people and shelf records are ongoing at April 15.',
          'Explicit-ID lookup baseline; no inference of the archivist role is needed and no difficult disambiguation claim is justified.'),
 'F_L2': ('Morgan North is the sole archivist and holds Folder 76; Morgan South is the treasurer and holds Folder 96.',
          'The role and folder assignments are simultaneously valid at April 15.',
          'A role-to-object lookup with recurring North/archivist mapping; this limited contrast does not generalize to arbitrary ambiguous names.'),
 'F_L3': ('The archivist is Morgan North, assigned Folder 77, stored on Amber Shelf; South and Folder 97 lead to Violet Shelf.',
          'The role, folder and shelf links are ongoing at April 15.',
          'Three linked facts support the answer, but repeated North/archivist/Amber patterns can permit shortcuts.'),
 'G_L1': ('Hollis uses Harbor Lodge on April 15; Meadow and Orchard belong to earlier intervals.',
          'April 15 belongs to Harbor from April 1 onward, not the March Meadow interval.',
          'Current-date lookup baseline; a correct answer is not evidence of broad temporal reasoning.'),
 'G_L2': ('Indigo uses Meadow Lodge on March 20, even though Harbor is the April location.',
          'The explicit March 20 question controls the proposition date; a true past answer is not an outdated-current error.',
          'Past-date selection without a demonstrated difficulty increase; distinguish historical truth from stale current claims.'),
 'G_L3': ('Jules uses Meadow Lodge on March 20 and Harbor Lodge on April 15; both requested values differ as the question states.',
          'The two answers are true in disjoint March and April intervals, not contradictory simultaneous facts.',
          'Two time-indexed slots test attribution and coverage; recurring locations and extra output burden remain limitations.'),
 'H_L1': ('The recent dialogue focuses on Parcel 121, whose delivery desk is Elm.',
          'The undated follow-up uses April 15, within the ongoing Parcel 121 interval.',
          'A valid simple follow-up baseline. Only one parcel exists, so context necessity is not demonstrated.'),
 'H_L2': ('The dialogue focuses on Parcel 122, assigned to Recipient 142, whose current desk is Ash rather than the earlier Elm desk.',
          'The question asks April 15; Ash starts April 10 after Elm ends April 9.',
          'A valid dated follow-up; only one parcel exists, so preceding context does not force selection among competing parcels.'),
 'H_L3': ('The final focus selects Parcel 111, assigned to Recipient 131, at Ash Desk; Parcel 151 instead leads to Recipient 171 and Oak Desk.',
          'The question asks April 10, the inclusive start of Recipient 131 at Ash after Elm ends April 9.',
          'Context distinguishes two supported desk answers. Two explicitly labelled User turns are retained; effects on Base continuation are unknown.'),
}


def proposals(dataset, master):
    by_id = {c['case_id']: c for c in dataset['cases']}
    if len(master) != 24 or len(by_id) != 24 or set(by_id) != {r['case_id'] for r in master}:
        raise ValueError('Expected the original 24 cases')
    rows = []
    for original in master:
        c = by_id[original['case_id']]
        key = c['case_id'].removeprefix('p1b_')
        derivation, temporal, limitation = NOTES[key]
        proof = [line for fid in c['expected_answer']['proof_fact_ids']
                 for line in c['trusted_evidence'].splitlines() if line.startswith(fid + ':')]
        if len(proof) != len(c['expected_answer']['proof_fact_ids']):
            raise ValueError('Missing quoted source link')
        answer = json.dumps(c['expected_answer']['components'], sort_keys=True)
        context = '\n'.join(c['context'])
        material = {'trusted_evidence':c['trusted_evidence'], 'current_question':c['question'],
                    'fixed_context':context, 'active_style':c['style_only'],
                    'supplemental_fact':c['supplemental_fact'], 'dated_history':c['history_dialogue']}
        def quoted(field, text=None):
            text = material[field] if text is None else text
            if text not in material[field]:
                raise ValueError('Quotation does not match its source')
            return {'field':field, 'verbatim':text}
        support = [quoted('trusted_evidence', p) for p in proof]
        current = c['speaker_name']
        temporal_axis = c['applicability']['temporal_consistency']
        reasons = {
          'evidence_sufficient': f'{c["case_id"]}: {derivation} The displayed chain supplies every requested component without outside knowledge.',
          'answers_unique': f'{c["case_id"]}: {derivation} No alternative source value is supported for this target at the same requested time; paraphrases remain valid.',
          'reference_answer_correct': f'{c["case_id"]}: {answer} follows from the cited ledger relations. {derivation} This validates the key, not a model reasoning path.',
          'temporal_interpretation_correct': f'{c["case_id"]}: {temporal} The prompt exposes the fictional reference clock.',
          'entities_clear': f'{c["case_id"]}: {derivation} The question and fixed context specify the referent; identical names are not silently treated as identical people.',
          'question_clear': f'{c["case_id"]}: The exact question quoted here requests {len(c["expected_answer"]["components"])} component(s), {", ".join(c["expected_answer"]["components"])}. {derivation}',
          'context_valid': (f'{c["case_id"]}: The quoted focus on Parcel 111 resolves "it" despite Parcel 151. The separate follow-up has an explicit User label and final Assistant stub; consecutive User turns are a disclosed format limitation, not evidence of model compliance.' if key == 'H_L3' else
              f'{c["case_id"]}: The quoted preceding dialogue is compatible with the current question about {current}. ' + (f'The parcel focus resolves "it", but {limitation}' if c['family']=='H' else 'The assistant asks which record to inspect, followed by the specified record question; context necessity is not assumed.')),
          'speaker_consistent': f'{c["case_id"]}: {current} is named in recent context, the bookmark fact and the dated residence speaker line. ' + ('Morgan North/South are explicitly distinct project entities, not replacement persona identities.' if c['family']=='F' else 'Object targets remain associated with that case. The style profile is descriptive; first-person role adoption is not guaranteed.'),
          'reference_stable_across_cells': f'{c["case_id"]}: {derivation} None of the quoted style, bookmark or dated residence additions replaces that trusted chain. Exact evidence/question/context are invariant in all eight recorded prompts.',
          'no_accidental_answer_leakage': f'{c["case_id"]}: The quoted style concerns expression, the bookmark is unrelated to the requested {", ".join(c["expected_answer"]["components"])}, and H supplies a 2026 residence. ' + ('That past residence is relevant, but does not supply the requested 2027 answer. Topic and past-fact cues remain intentional intervention content.' if c['family']=='E' else 'H does not answer this non-residence query. Common names/context may identify targets but do not add the answer outside shared evidence.'),
          'no_unplanned_contradictions': f'{c["case_id"]}: {temporal} The November 15, 2026 history asserts past residence, not a present claim. ' + ('The Alderwick history agrees with the explicitly recorded 2026 residence interval.' if c['family']=='E' else 'Residence, bookmark ownership and the requested source relation are distinct; no incompatible same-time value is asserted.'),
          'applicability_correct': f'{c["case_id"]}: This evidence-grounded request supports factual/relevance/coherence review; temporal eligibility is {temporal_axis}. ' + ('The question requires interval or past/current selection.' if temporal_axis else 'A static current lookup is not a temporal-change endpoint under the frozen applicability policy.') + ' Both fidelity endpoints remain false because there is no validated style/behavior reference.',
          'demand_description_appropriate': f'{c["case_id"]}: {limitation} The original demand/risk field qualifies designed level, and empirical difficulty remains UNTESTED. No correct response will certify the intended cognitive path.',
        }
        quotes = {k:support for k in CHECKS}
        for k in ('entities_clear','question_clear'):
            quotes[k] = support + [quoted('current_question'), quoted('fixed_context')]
        quotes['context_valid'] = [quoted('fixed_context'),quoted('current_question')]
        for k in ('speaker_consistent','no_accidental_answer_leakage','no_unplanned_contradictions','reference_stable_across_cells'):
            quotes[k] = support + [quoted('active_style'),quoted('supplemental_fact'),quoted('dated_history')]
        row = dict(original)
        row.update(ai_proposal_version=VERSION, ai_provenance='AI-assisted source review; not human approval',
                   ai_case_decision='ACCEPT', ai_decision_scope='Bounded development calibration only; subject to explicit researcher confirmation',
                   ai_reference_derivation=derivation, ai_temporal_explanation=temporal,
                   ai_case_limitations=limitation,
                   ai_shared_limitations='Designed difficulty untested; style nested in speaker; uniform bookmark; history relevance confounded with family; 96-token output may censor replies; no independent confirmatory data.',
                   ai_unresolved_issues='Researcher confirmation of all 13 proposed judgments and the stated limited interpretation; no identified source/key defect requiring a stimulus revision.',
                   ai_supporting_quotations=json.dumps(quotes,ensure_ascii=False,sort_keys=True),
                   researcher_confirmation='')
        for k in CHECKS:
            row['ai_proposed_'+k] = 'PASS'
            row['ai_explanation_'+k] = reasons[k]
        rows.append(row)
    return rows


def confirmed_copy(master, proposal, submitted):
    """Expand only explicit per-case confirmation, retaining original submission."""
    originals = {r['case_id']:r for r in master}
    proposed = {r['case_id']:r for r in proposal}
    if len(submitted)!=24 or {r['case_id'] for r in submitted}!=set(originals):
        raise ValueError('24 unique case confirmations required')
    editable = {'researcher_confirmation','reviewer_id','review_method','reviewed_utc','reviewer_notes'}
    converted=[]
    for r in submitted:
        p = proposed[r['case_id']]
        if r.keys()!=p.keys() or any(r[k]!=p[k] for k in p.keys()-editable):
            raise ValueError('Proposal or original field changed; preserve source and use the original manual review form for revised judgments')
        if r['researcher_confirmation']!=CONFIRM:
            raise ValueError('Every case needs explicit confirmation of all proposed judgments')
        if not r['reviewer_id'].strip() or not r['review_method'].strip():
            raise ValueError('Actual reviewer and method required')
        if r['reviewed_utc']:
            datetime.fromisoformat(r['reviewed_utc'].replace('Z','+00:00'))
        result=dict(originals[r['case_id']])
        result.update({k:r[k] for k in ('reviewer_id','review_method','reviewed_utc','reviewer_notes')})
        result['review_method'] += '; explicit confirmation of AI-proposed labels and limited interpretation'
        result['researcher_decision']=p['ai_case_decision']
        result['evidence_quotations']=p['ai_supporting_quotations']
        for k in CHECKS:
            result['check_'+k]=p['ai_proposed_'+k]
        converted.append(result)
    validate_reviews(master,converted)
    return converted

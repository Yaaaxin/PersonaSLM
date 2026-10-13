"""Author the pre-output English synthetic P1 development material once."""
import json
from pathlib import Path
import random
from personaslm.journal import atomic_json,utc_now
from personaslm.p1 import VERSION,validate_dataset,wave_order

STYLES=[
 ('brevity','The speaker favors brief replies with one concise clause per answer.'),
 ('brevity','The speaker expresses the requested point briefly, using compact sentences.'),
 ('formal','The speaker uses formal phrasing and fully written words rather than contractions.'),
 ('formal','The speaker prefers a formal register with complete, uncontracted sentences.'),
 ('conversational','The speaker uses conversational wording and ordinary contractions in replies.'),
 ('conversational','The speaker prefers informal phrasing with natural contractions when speaking.'),
 ('plain_lexicon','The speaker prefers everyday words such as help rather than assist.'),
 ('plain_lexicon','The speaker favors familiar words such as use rather than utilize.'),
 ('separated_rhythm','The speaker separates successive ideas into short sentences with clear pauses.'),
 ('separated_rhythm','The speaker gives each successive idea its own sentence instead of chaining clauses.'),
 ('acknowledgment','The speaker briefly acknowledges a request before giving the requested answer.'),
 ('acknowledgment','The speaker begins replies with a short acknowledgment, then addresses the request.')]

def build():
    seed=713019;rng=random.Random(seed)
    names=['Avery','Cameron','Ellis','Harper','Jordan','Kendall','Lennox','Marlowe','Parker','Quinn','Reese','Sutton']
    cities=['Oxford','Cambridge','Derby','York','Bath','Exeter','Durham','Chester','Lincoln','Norwich','Lancaster','Plymouth']
    old=['Leeds','Bristol','Hull','Cardiff','Newcastle','Sheffield','Manchester','Liverpool','Nottingham','Leicester','Worcester','Carlisle']
    clubs=['Maple Reading Circle','Cedar Reading Circle','Willow Reading Circle','Birch Reading Circle','Aspen Reading Circle','Elm Reading Circle','Oak Reading Circle','Pine Reading Circle','Rowan Reading Circle','Beech Reading Circle','Alder Reading Circle','Hazel Reading Circle']
    possessions=['a red umbrella','a green notebook','a wooden chess set','a blue bicycle','a small telescope','a striped scarf','a yellow raincoat','a folding easel','a silver thermos','a ceramic mug','a canvas backpack','a leather bookmark']
    for items in [names,cities,old,clubs,possessions]:rng.shuffle(items)
    rows=[];personas=[]
    for i,(category,style) in enumerate(STYLES):
        pid=f'p1_speaker_{i+1:02d}';name=names[i]
        personas.append({'persona_id':pid,'speaker_name':name,'style_category':category,'style_realization':'A' if i%2==0 else 'B','style_only':style,
            'language':'en','provenance':'New fictional synthetic profile; no real conversation or translation',
            'counterbalance_note':'Independent seeded permutations of names, cities, clubs and possessions; style remains nested in speaker'})
        facts=[{'fact_id':pid+'_old_city','attribute':'current_city','value':old[i],'valid_from':'2025-01-01','valid_until':'2026-09-30'},
            {'fact_id':pid+'_current_city','attribute':'current_city','value':cities[i],'valid_from':'2026-10-01','valid_until':None},
            {'fact_id':pid+'_club','attribute':'reading_group','value':clubs[i],'valid_from':'2024-01-01','valid_until':None},
            {'fact_id':pid+'_possession','attribute':'supplemental_possession','value':possessions[i],'valid_from':'2024-01-01','valid_until':None}]
        evidence=f'Verified record as of 2026-10-13: {name} currently lives in {cities[i]}, valid from 2026-10-01 onward. {name} is a member of the {clubs[i]}, valid from 2024-01-01 onward.'
        for family in 'ABCD':
            context={'A':[f'User: I am checking the current residence record for {name}.','Assistant: We can use the verified current record.'],
                'B':[f'User: I am updating the reading-group membership list for {name}.','Assistant: The verified membership record can help.'],
                'C':[f'User: We are drafting a welcome message for {name}.','Assistant: What would you like the message to say?'],
                'D':[f'User: My address note for {name} is from before the October move.','Assistant: The delivery destination should use the record valid now.']}[family]
            question={'A':f'Where does {name} currently live?',
                'B':f'Which reading group is {name} a member of?',
                'C':f'Please write a friendly welcome greeting for {name} without adding any biographical claims.',
                'D':f'Following the October move, which city does {name} currently live in for the delivery?'}[family]
            rows.append({'case_id':f'{pid}_{family}','persona_id':pid,'speaker_name':name,'family':family,
                'style_category':category,'style_realization':'A' if i%2==0 else 'B','evaluation_date':'2026-10-13','history_date':'2026-09-15',
                'task_type':{'A':'current_city_update','B':'stable_membership','C':'nonfactual_greeting','D':'current_city_followup'}[family],
                'context':context,'question':question,'trusted_evidence':evidence,
                'expected_answer':None if family=='C' else (clubs[i] if family=='B' else cities[i]),'facts':facts,
                'style_only':style,'supplemental_fact':f'{name} owns {possessions[i]}.',
                'history_dialogue':f'Historical dialogue (2026-09-15):\nUser: Where were you living then?\n{name}: I was living in {old[i]} at that time.',
                'neutral_style':'UNSELECTED_PENDING_TOKENIZER_AND_REVIEW','neutral_history':'UNSELECTED_PENDING_TOKENIZER_AND_REVIEW',
                'applicability':{'response_relevance':True,'factual_consistency':family!='C','temporal_consistency':family in 'AD',
                    'conversational_coherence':True,'linguistic_fidelity':False,'behavioral_fidelity':False},
                'applicability_reason':'Factual: A/B/D; temporal: dated-current-update A/D; relevance/coherence: all; fidelity lacks independent reference ground truth',
                'wave1_selected':family=='ABCD'[i%4],'language':'en','source_type':'fictional_synthetic','split':'p1_development_only'})
    return {'version':VERSION,'created_utc':utc_now(),'language':'en','source_type':'fictional_synthetic',
        'allocation_seed':seed,'evaluation_reference_date_is_synthetic':True,'personas':personas,'cases':rows,
        'wave1_selection_rule':'For speaker index i=0..11, select family ABCD[i mod 4], before any model response. One case per speaker; three per family.',
        'confirmatory_test':False,'limitations':['Two same-intent realizations per category are different speakers, not isolated paraphrase effects',
            'Within-family wording is mostly fixed; four task families do not imply broad task coverage','History is stale but genuinely true at its stated date; no simultaneous contradiction intervention']}

if __name__=='__main__':
    dataset=build();audit=validate_dataset(dataset);order=wave_order(dataset)
    Path('docs/validation/p1').mkdir(exist_ok=True)
    atomic_json(Path('data/synthetic/p1_development_v1.json'),dataset)
    atomic_json(Path('docs/validation/p1/manipulation_v1.json'),audit)
    print(json.dumps({'personas':len(dataset['personas']),'cases':len(dataset['cases']),'factorial_prompts_checked':audit['prompt_count'],'wave_requests':len(order)}))

"""Render official pinned templates without loading model weights or generating.

Candidate mapping only: one user message contains the unchanged Base task body,
excluding its final Assistant: completion marker. No extra priority instruction.
Actual Instruct GGUF tokenization/runtime remain unverified.
"""
from pathlib import Path
import sys
from p1d_design import read, write, sha, th
from p1d_scientific_audit import DEST, BANK

RUNTIME=Path('results/p1d_scientific_validation/v1/template_runtime')
META=Path('docs/validation/p1d/development_readiness_v1/official_instruct_metadata')

def environment():
    if RUNTIME.exists():sys.path.insert(0,str(RUNTIME.resolve()))
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    env=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True,extensions=['jinja2.ext.loopcontrols'])
    def fail(message):raise ValueError(message)
    env.globals['raise_exception']=fail
    return env

def render(template,messages):
    return environment().from_string(template).render(messages=messages,tools=None,add_generation_prompt=True,enable_thinking=False,add_vision_id=False)

def messages_for_base(prompt):
    suffix='\nAssistant:'
    if not prompt.endswith(suffix):raise ValueError('Unexpected Base completion suffix')
    body=prompt[:-len(suffix)]
    if any(marker in body for marker in ('<|im_start|>','<|im_end|>')):raise ValueError('Reserved official role marker in source content')
    return [{'role':'user','content':body}]

def main():
    template=(META/'chat_template.jinja').read_text(encoding='utf-8')
    if sha(META/'chat_template.jinja')!='0286b273dc0e7dbcc080469bf5b8e57b329c135db0de8a45cb16f80a8b0c4ce6':raise ValueError('Template changed')
    embedded=read(META/'tokenizer_config.json')['chat_template']
    ps={r['candidate_request_id']:r for r in read(BANK/'base_candidate_prompts_v1.json')}
    inventory=read('docs/validation/p1d/development_readiness_v1/full_allocation_planning_inventory_v2.json')['rows'];out=[]
    for r in inventory:
        if r['model_arm']!='Instruct':continue
        p=ps[r['base_candidate_reference']];messages=messages_for_base(p['prompt'])
        rendered=render(template,messages);other=render(embedded,messages)
        if messages[0]['content'] not in rendered:raise ValueError('Task body changed')
        if not rendered.endswith('<|im_start|>assistant\n<think>\n\n</think>\n\n'):raise ValueError('Non-thinking generation prefix mismatch')
        out.append({'planning_id':r['planning_id'],'case_id':r['case_id'],'speaker_id':r['speaker_id'],'condition':r['condition'],
            'base_prompt_sha256':p['prompt_sha256'],'messages':messages,'rendered_prompt':rendered,'rendered_prompt_sha256':th(rendered),
            'embedded_template_same_for_this_mapping':rendered==other,'instruct_input_token_ids':None,'generation_authorized':False})
    probe=[{'role':'user','content':'A development template probe.'},{'role':'assistant','content':'A reply without reasoning.'}]
    write(DEST/'instruct_rendered_candidates_v1.json',{'version':'p1d_instruct_rendered_candidates_v1','status':'CANDIDATE_MAPPING_NOT_FROZEN_NOT_TOKENIZED',
        'source_template_sha256':sha(META/'chat_template.jinja'),'rows':out,'new_model_generations':0,
        'mapping':'One user role contains exact Base task body minus terminal Assistant marker. Fixed dialogue stays quoted task content; not promoted to actual chat turns. No added system message.',
        'configuration_confound':'Official role/thinking prefixes and task-message packaging differ from Base; comparison is model-plus-template configuration.'})
    import importlib.metadata
    packages={p:importlib.metadata.version(p) for p in ('Jinja2','MarkupSafe')}
    write(DEST/'official_template_rendering_verification_v1.json',{'rendered_candidates':len(out),'all_same_task_body':True,
        'all_embedded_template_equal_for_single_user_mapping':all(r['embedded_template_same_for_this_mapping'] for r in out),
        'assistant_after_user_probe_differs':render(template,probe)!=render(embedded,probe),'packages':packages,
        'package_file_sha256':{p.as_posix():sha(p) for p in sorted(RUNTIME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
        'model_loaded':False,'native_instruct_tokenization_verified':False,'backend_chat_renderer_equivalence_verified':False,
        'limitation':'Direct Jinja sandbox rendering of official bytes, not Transformers or llama.cpp/minja equivalence. No weights or inference; actual GGUF template precedence and native role-token IDs remain final preflight checks.'})
    print({'rendered':len(out),'same_embedded_for_mapping':all(r['embedded_template_same_for_this_mapping'] for r in out),'packages':packages,'new_inference':0})

if __name__=='__main__':main()

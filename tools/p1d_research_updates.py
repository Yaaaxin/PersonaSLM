"""Focused primary-source novelty/implementation update; no inference or adoption."""
from pathlib import Path
import p1d_budget_calibration as b

OUT=Path('docs/validation/p1d/final_preparation_v1')
PAPERS=[
 {'title':'Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning','authors':'Saibo Geng; Martin Josifoski; Maxime Peyrard; Robert West','status':'EMNLP 2023 conference paper','id':'2023.emnlp-main.674','source':'https://aclanthology.org/2023.emnlp-main.674.pdf','verification':'Full methods, experimental setup/results and latency/empty-output discussion inspected',
  'method':'Input-dependent grammars and incremental parsing mask invalid continuations. LLaMA 7/13/33B and Vicuna 7/13B; information extraction, entity disambiguation and constituency parsing.',
  'finding':'Reported structure/task gains, but grammar validity alone does not make parsing semantically accurate; empty-output issues discussed.',
  'overlap':'Grammar-guided component slots are established, not a new PersonaSLM algorithm.',
  'missing_test':'CPU 2B ledger dialogue, persona fidelity and independently adjudicated answer loss.'},
 {'title':'The Hidden Cost of Structure: How Constrained Decoding Affects Language Model Performance','authors':'Maximilian Schall; Gerard de Melo','status':'RANLP 2025 conference paper','id':'2025.ranlp-1.124','source':'https://aclanthology.org/2025.ranlp-1.124.pdf','verification':'Methods, models, metrics and main results inspected',
  'method':'Eleven 4–8B Base/Instruct models; Outlines/vLLM, generation and classification tasks, model/task-specific prompt selection.',
  'finding':'Benefits and costs differ across model/task types; structural compliance does not establish content correctness.',
  'overlap':'Separating structure and semantics is prior art; do not claim novelty for that distinction alone.',
  'missing_test':'Fixed evidence and persona packages under equal CPU budgets; published GPU costs do not predict local latency.'},
 {'title':'Lost in Space: Finding the Right Tokens for Structured Output','authors':'Sil Hamilton; David Mimno','status':'GEM workshop proceedings 2026','id':'10.18653/v1/2026.gem-main.18','source':'https://aclanthology.org/2026.gem-main.18.pdf','verification':'Methods, tokenizer-format variables and main result tables inspected',
  'method':'Eight Instruct models, four NLP datasets, five numeric/label formats and whitespace variants; llama.cpp GBNF, q8_0, CUDA.',
  'finding':'Token representation and format conventions influence measured performance.',
  'overlap':'Grammar, token boundaries and whitespace are substantive configuration variables, not neutral implementation details.',
  'missing_test':'Dialogue answer completeness and persona fidelity on independently authored inputs; no transfer guarantee from classification.'},
 {'title':'The Hidden Cost of Structured Generation in LLMs: Draft-Conditioned Constrained Decoding','authors':'Avinash Reddy; Thayne T. Walker; Jaime S. Ide; Amrit Singh Bedi (PMLR record)','status':'ICML 2026, PMLR 306','id':'pmlr-v306-reddy26a; arXiv:2603.03305v2','source':'https://proceedings.mlr.press/v306/reddy26a.html','methods_source':'https://arxiv.org/html/2603.03305v2','implementation':'https://github.com/avinashreddydev/dccd',
  'verification':'Venue record verified; venue PDF fetch failed. arXiv v2 algorithm, experiments and Appendix L inspected; byte equivalence to venue PDF NOT VERIFIED. arXiv lists James S. Ide; retain metadata discrepancy.',
  'method':'Unconstrained draft followed by constrained realization, optionally multiple drafts; six 1–14B models, four reasoning datasets, budget-matched ablation.',
  'finding':'Reported structured-accuracy gains; two passes add cost and wrong drafts usually remain wrong.',
  'overlap':'Draft-then-verify/constrain is a mandatory baseline, not original merely when adapted to CPU.',
  'missing_test':'Equal total tokens/calls, persona retention, missing-answer recovery and CPU latency in this setting.'},
 {'title':'Constrained Decoding Eliminates Structural Failures in Small LLMs but Reveals a Scale-Dependent Semantic Gap','authors':'Akash Chavan','status':'Preprint; peer review NOT ESTABLISHED','id':'arXiv:2609.23742v1','source':'https://arxiv.org/html/2609.23742v1','verification':'Methods, result tables, failure archetypes and limitations inspected',
  'method':'Five 0.6–4B models, 14 authored tasks, greedy native/Outlines/XGrammar; structural and normalized semantic scoring.',
  'finding':'Reported schema repair with remaining semantic failures; limited task set and selected model configuration scope.',
  'overlap':'Small-model structural/semantic separation already directly studied; 100% reported schema validity is not a universal guarantee.',
  'missing_test':'Independent free-dialogue boundaries, dated persona interference and task delivery under fixed evidence.'}
]

def run():
    parent=Path('docs/validation/p1d/scientific_validation_v1/related_work_monitor_delta_v5.json')
    delta={'version':'related_work_monitor_delta_v6','parent_path':parent.as_posix(),'parent_sha256':b.sha256(parent),
        'software_recorded_utc':b.utc_now(),'scope':'Focused methods/code follow-up plus new structured-generation competitors; no claim that all earlier papers were reread.',
        'search_queries':['site.aclanthology.org grammar constrained decoding structured outputs language models boundary JSON schema evaluation',
            'site.arxiv.org "response boundary" language model generation turn','site.aclanthology.org "Stop" "end-of-turn" language model generation',
            '"Draft-Conditioned Constrained Decoding" arxiv'],
        'new_primary_papers':PAPERS,
        'implementation_checks':[
            {'work':'LongMemEval','source':'https://raw.githubusercontent.com/xiaowu0162/LongMemEval/main/src/index_expansion/temp_query_search_pruning.py',
             'checked':'Source read, not executed. Extracts query range with an LLM; expands by two days; places out-of-range sessions after retained sessions while preserving order.',
             'implication':'Our supplied-date hard filter is an engineering baseline, not full replication. Branch is movable; implementation commit not pinned.'},
            {'work':'FPPS','source':'https://github.com/zhengyi-ai/ACL2026','paper':'https://aclanthology.org/2026.findings-acl.395.pdf',
             'checked':'Paper method and official repository structure/readme; prober/activation steering, not evidence-priority prompting.',
             'implication':'No local GGUF activation adaptation or full reproduction executed.'},
            {'work':'CoVe','source':'https://aclanthology.org/2024.findings-acl.212.pdf','checked':'Independent/factored verification and revision require additional model work; a supplied-claim checker is not CoVe.'},
            {'work':'RARR','source':'https://aclanthology.org/2023.acl-long.910.pdf','implementation':'https://github.com/anthonywchen/RARR',
             'checked':'Search, attribution and editing pipeline; no hosted-model or external-search execution. Closed-ledger adaptation would differ.'},
            {'work':'What to Admit and How to Present','source':'https://arxiv.org/html/2610.11188v1','status':'Preprint',
             'checked':'Section 3 admission/presentation: factual/persona-consistency judgments and controlled presentation. Admission and formatting are not novel in themselves.'}],
        'novelty_status':'NO_SUPPORTED_ORIGINAL_ALGORITHM','external_implementations_executed':False}
    b.save(OUT/'related_work_monitor_delta_v6.json',delta)
    prior=Path('docs/validation/p1d/scientific_validation_v1/algorithm_opportunity_registry_update_v4.json')
    registry=b.load(prior)
    notes={
      'temporal_entity_verification':('Fair top-1 BM25/temporal comparison on 16 development cases; supplied-date filtering resolves this curated selection test.','No demonstrated gap beyond existing temporal/entity selection; retain free-text extraction as unvalidated.'),
      'history_admission':('BM25 ties explicitly averaged, equal one-item retention. Time+BM25 matches entity+time+BM25 on supplied metadata.','Simple baseline succeeds here; no novelty or downstream generation/fidelity gain established.'),
      'persona_evidence_separation':('FPPS activation baseline verified in prior art; no runtime access implemented.','Need complete fair steering/admission baselines; do not infer persona causation from failed delivery.'),
      'component_verification':('Budget review separates a promise from delivered components. Existing date-scope checker remains an adaptation.','CoVe, RARR and DCCD overlap; no proven mathematical/computational novelty.'),
      'response_boundary':('Prefix-locality prototype returns 64/72 P1c candidates, adding none of the eight unresolved cases.','Negative empirical result retained. Independent boundary labels and generation-level template/stop comparison needed.'),
      'interaction_aware_conditioning':('No new E/V effect-sign selection or independent interaction evidence.','Routing remains deferred; no adaptive-conditioning prototype justified.')}
    for r in registry['rows']:
        r['development_update'],r['current_gap_decision']=notes[r['candidate']]
        r['algorithm_generation_calls_this_update']=0
        r['independently_supported_original_contribution']=False
    b.save(OUT/'algorithm_opportunity_registry_update_v5.json',{'version':'algorithm_opportunity_registry_update_v5',
        'parent_path':prior.as_posix(),'parent_sha256':b.sha256(prior),'rows':registry['rows'],
        'retrieval_results':str(b.OUT/'offline_retrieval_v1/summary_v1.json'),
        'boundary_results':str(b.OUT/'offline_baseline_v1/summary_v1.json')})
    print({'new_primary_papers':len(PAPERS),'algorithm_candidates':len(registry['rows']),'novel_algorithm_claims':0})

if __name__=='__main__':run()

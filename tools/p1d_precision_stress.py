"""Reproducible selected-design stress simulation; no generated model responses."""
import random
import statistics
from p1d_precision import one
from p1d_design import OUT,read,write,sha

def run():
    rows=[]
    for n in (96,144):
        for cluster,pair in ((.4,.25),(.7,0)):
            rng=random.Random(716500+n+int(cluster*100))
            trials=[one(rng,n,.5,cluster,pair,'none',0) for _ in range(512)]
            for c in ('E','V','ExV'):
                rows.append({'speakers':n,'cluster_sharing_not_ICC':cluster,'pair_sharing':pair,'prevalence':.5,'effect':0,'replicates':512,'contrast':c,
                    'median_halfwidth':statistics.median(t[c]['halfwidth'] for t in trials),
                    'median_six_comparison_halfwidth':statistics.median(t[c]['familywise_halfwidth'] for t in trials),
                    'coverage':statistics.mean(t[c]['complete_data_coverage'] for t in trials)})
    previous=read(OUT/'precision_stress_v1.json')
    if previous['rows']!=rows:raise ValueError('Deterministic reconstruction differs')
    write(OUT/'precision_stress_reconstruction_v1.json',{'rows_equal':True,'rows':len(rows),'source_sha256':sha(__file__),
        'input_result_sha256':sha(OUT/'precision_stress_v1.json'),'new_generations':0})
    print('12 stress summaries reconstructed exactly from 2048 simulated trials')

if __name__=='__main__':run()

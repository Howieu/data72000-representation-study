"""Read-only checks of recorded outputs against explicitly located manuscript claims."""
import csv
import re
from pathlib import Path
from statistics import mean
ROOT = Path(__file__).resolve().parents[1]
rows = []
def read(name):
    with (ROOT / name).open() as f:
        return list(csv.DictReader(f))
def check(section, context, printed, path, value, digits=3):
    source = ROOT / 'dissertation/overleaf/sections' / (section + '.tex')
    lines = source.read_text().splitlines()
    locations = [str(i+1) for i,line in enumerate(lines) if printed in line and context in line]
    matched = abs(float(printed.replace(',',''))-float(value)) <= 0.5 * 10**(-digits) + 1e-12
    status = 'Yes' if matched and locations else ('Unlocated' if not locations else 'NO')
    rows.append([f'{section}.tex:{",".join(locations)} ({context})',printed,path,f'{value:.12g}',status,'Retain' if status=='Yes' else 'Inspect claim/context'])
p='results/retailrocket/selected_configurations.csv'
values={('compact','classix'):('0.595','1.057','4285.5'),('rich','classix'):('0.291','0.859','1516.9'),('compact','kmeans'):('0.560','0.775','10459.1'),('rich','kmeans'):('0.351','1.040','3923.4')}
for row in read(p):
    if row['selection']!='deployment_acceptable':continue
    for field,printed,dp in zip(['silhouette','davies_bouldin','calinski_harabasz'],values[row['representation'],row['method']],[3,3,1]):
        check('paired_results','',printed,p+f" [{row['representation']}/{row['method']}/{field}]",float(row[field]),dp)
p='results/retailrocket/resampling_stability.csv'
for rep,method,printed in [('compact','classix','0.985'),('rich','classix','0.965'),('compact','kmeans','0.988'),('rich','kmeans','0.995')]:
    selected=[r for r in read(p) if r['selection']=='deployment_acceptable' and r['representation']==rep and r['method']==method]
    assert len(selected)==10
    check('paired_results','',printed,p+f' [mean {rep}/{method}, n=10]',mean(float(r['ari_overlap']) for r in selected))
p='results/retailrocket/exkmc_oos_fidelity.csv'
for rep,budget,printed in [('compact',4,'0.9448'),('rich',4,'0.9650'),('compact',16,'0.9924'),('rich',16,'0.9747')]:
    selected=[r for r in read(p) if r['representation']==rep and int(r['k_prime'])==budget]
    assert len(selected)==5 and all(r['test_rows_used_for_selection']=='0' for r in selected)
    check('explanation_results','',printed,p+f' [mean {rep}, leaves={budget}, n=5]',mean(float(r['test_fidelity']) for r in selected),4)
p='results/sensitivity/session_window_sensitivity.csv'
for r in read(p):
    if r['window_minutes']=='30':continue
    printed={('kmeans','15'):'0.976',('classix','15'):'0.971',('kmeans','60'):'0.985',('classix','60'):'0.959'}[r['algorithm'],r['window_minutes']]
    check('sensitivity_limitations','',printed,p+f" [{r['algorithm']}/{r['window_minutes']} minutes]",float(r['ari']))
p='results/sensitivity/feature_ablation.csv'
for r in read(p):
    key=(r['algorithm'],r['dropped_feature'])
    printed={('classix','distinct_top_categories'):'0.189',('kmeans','distinct_top_categories'):'0.516',('classix','top_category_share'):'0.238',('kmeans','top_category_share'):'0.517'}.get(key)
    if printed:check('sensitivity_limitations','',printed,p+f' [{key}]',float(r['ari']))
compact=read('data/derived/compact_features.csv');rich=read('data/derived/rich_features.csv')
assert len(compact)==len(rich)==11719
schema=read('data/derived/feature_schema.csv')
assert len(schema)==12
assert sum(r['block']=='compact_transaction' for r in schema)==3
assert set(compact[0])=={'visitorid','snapshot_id'} | {r['feature'] for r in schema if r['block']=='compact_transaction'}
assert set(rich[0])=={'visitorid','snapshot_id','category_coverage_flag'} | {r['feature'] for r in schema}
assert len({r['visitorid'] for r in compact})==11719
assert all(all(a[k]==b[k] for k in a) for a,b in zip(compact,rich))
check('data_representation','', '11,719','data/derived/{compact,rich}_features.csv [row count; same IDs and compact values]',len(compact),0)

import json
from collections import Counter
from statistics import median
p='results/retailrocket/paired_partition_comparison.csv'
for r in read(p):
    if r['comparison']=='independent_deployment_selection':
        for field,printed in zip(['ari','nmi','vi'], {'kmeans':['0.014','0.089','1.691'],'classix':['0.068','0.054','0.693']}[r['method']]):
            check('paired_results','',printed,p+f" [{r['method']}/{field}]",float(r[field]))
a=[float(r['ari']) for r in read(p) if r['comparison']=='fixed_k']
check('paired_results','','0.012',p+' [fixed K minimum]',min(a))
check('paired_results','','0.113',p+' [fixed K maximum]',max(a))
grid=read('results/retailrocket/candidate_grid.csv')
def acceptable(r):
    import math
    return r['internal_valid']=='True' and 2<=int(r['n_clusters'])<=12 and float(r['noise_fraction'])<=0.2 and float(r['largest_non_noise_cluster_share'])<=0.95 and all(math.isfinite(float(r[f])) for f in ['silhouette','davies_bouldin','calinski_harabasz'])
ids={rep:{r['candidate_id'] for r in grid if r['representation']==rep and r['method']=='classix' and acceptable(r)} for rep in ['compact','rich']}
common=ids['compact'] & ids['rich']
a=[float(r['ari']) for r in read(p) if r['comparison']=='fixed_classix_parameter' and r['parameter_value'] in common]
assert len(a)==41, len(a)
for printed,val in [('41',len(a)),('-0.051',min(a)),('0.392',max(a)),('-0.023',median(a))]:
    check('paired_results','',printed,p+' [CLASSIX matched acceptable settings]',val,0 if printed=='41' else 3)
p='results/retailrocket/cluster_transition_matrix.csv'
for method,printed in [('kmeans','54.61'),('classix','18.66')]:
    a=[r for r in read(p) if r['method']==method]
    value=100*sum(int(r['n_customers']) for r in a if r['migration_flag']=='True')/sum(int(r['n_customers']) for r in a)
    check('paired_results','',printed,p+f' [{method} migrated percent]',value,2)
p='results/retailrocket/selected_configurations.csv'
for r in read(p):
    context=f" [{r['representation']}/{r['method']}/{r['selection']}]"
    sizes=json.loads(r['cluster_sizes'])
    if r['selection']=='deployment_acceptable':
        for val in sizes.values():
            printed=f'{val:,}'
            check('paired_results','',printed,p+context+' cluster size',val,0)
        printed={('compact','classix'):'0.909',('rich','classix'):'0.898',('compact','kmeans'):'0.664',('rich','kmeans'):'0.579'}[r['representation'],r['method']]
        check('paired_results','',printed,p+context+' largest share',float(r['largest_non_noise_cluster_share']))
    elif (r['representation'],r['method'])!=('rich','kmeans'):
        val=max(sizes.values());check('paired_results','',f'{val:,}',p+context+' largest size',val,0)
        printed={('compact','classix'):'0.899',('rich','classix'):'0.792',('compact','kmeans'):'0.850'}[r['representation'],r['method']]
        check('paired_results','',printed,p+context+' silhouette',float(r['silhouette']))
p='results/retailrocket/classix_provenance.json';data=json.loads((ROOT/p).read_text())
labels=read('results/retailrocket/selected_labels.csv')
for rep,printed in [('compact','131'),('rich','559')]:
    v=data[rep];check('explanation_results','',printed,p+f' [{rep} group count]',len(v['groups']),0)
    assert len(v['customer_trace'])==11719
    assert len(v['native_public_attributes']['groups_'])==11719
p='results/retailrocket/exkmc_oos_fidelity.csv'
for rep,budget,field,printed,dp in [('compact',4,'train_fidelity','0.9466',4),('rich',4,'train_fidelity','0.9639',4),('compact',4,'mean_conditions_per_rule','2.25',2),('rich',4,'mean_conditions_per_rule','2.25',2),('compact',16,'max_depth','6.6',1),('rich',16,'max_depth','6.4',1),('compact',16,'mean_conditions_per_rule','4.84',2),('rich',16,'mean_conditions_per_rule','4.74',2)]:
    a=[r for r in read(p) if r['representation']==rep and int(r['k_prime'])==budget]
    check('explanation_results','',printed,p+f' [{rep}/{budget} mean {field}]',mean(float(r[field]) for r in a),dp)
for rep,lo,hi in [('compact','0.9416','0.9480'),('rich','0.9599','0.9697')]:
    a=[float(r['test_fidelity']) for r in read(p) if r['representation']==rep and r['k_prime']=='4']
    check('explanation_results','',lo,p+f' [{rep}/4 minimum]',min(a),4)
    check('explanation_results','',hi,p+f' [{rep}/4 maximum]',max(a),4)
p='results/retailrocket/exkmc_train_selected_oos_fidelity.csv'
a=[r for r in read(p) if r['representation']=='compact' and r['k_prime']=='2']
check('explanation_results','','0.9985',p+' [compact selected-K mean test fidelity]',mean(float(r['test_fidelity']) for r in a),4)
p='results/sensitivity/pca_sensitivity.csv'
for r in read(p):
    if r['space']=='rich_named':continue
    check('sensitivity_limitations','','91.32',p+' [variance percent]',100*float(r['cumulative_explained_variance']),2)
    method=r['algorithm']
    for field,printed in [('reference_ari',{'kmeans':'0.995','classix':'0.920'}[method]),('silhouette',{'kmeans':'0.390','classix':'0.304'}[method]),('resampling_ari_mean',{'kmeans':'0.995','classix':'0.987'}[method])]:
        check('sensitivity_limitations','',printed,p+f' [{method}/{field}]',float(r[field]))
    assert int(r['n_components'])==6 and r['use_for_rules']=='False'
p='results/sensitivity/classix_perturbation_stability.csv'
for rep,sigma,avg,mn in [('compact',0.01,'0.999','0.996'),('rich',0.001,'0.995','0.985'),('rich',0.01,'0.985','0.962')]:
    a=[float(r['ari']) for r in read(p) if r['representation']==rep and float(r['sigma'])==sigma]
    assert len(a)==10
    check('sensitivity_limitations','',avg,p+f' [{rep}/{sigma} mean]',mean(a))
    check('sensitivity_limitations','',mn,p+f' [{rep}/{sigma} minimum]',min(a))
for r in read(p):
    if (r['representation']=='compact' and float(r['sigma'])<=0.001) or (r['representation']=='rich' and float(r['sigma'])<=0.0001):assert float(r['ari'])==1
p='results/sensitivity/permutation_dimension_control.csv'
for r in read(p):
    if r['algorithm']=='kmeans' and r['added_permuted_features']=='9':
        check('sensitivity_limitations','','0.017',p+' [K Means nine dimensions ARI]',float(r['ari']))
        check('sensitivity_limitations','','0.127',p+' [K Means nine dimensions silhouette]',float(r['silhouette']))
    if r['algorithm']=='classix' and r['added_permuted_features']=='1':assert int(r['n_clusters'])==1 and float(r['ari'])==0
p='results/sensitivity/feature_ablation_selected.csv'
for r in read(p):
    if r['selection']!='deployment_acceptable':continue
    key=r['method'],r['scenario_id']
    val={('classix','drop_feature_distinct_top_categories'):'0.153',('kmeans','drop_feature_distinct_top_categories'):'0.728',('classix','drop_block_category_behaviour'):'0.126',('kmeans','drop_block_category_behaviour'):'0.729'}.get(key)
    if val:check('sensitivity_limitations','',val,p+f' [{key}/ARI vs rich]',float(r['ari_vs_rich_deployment']))
assert len(read('results/sensitivity/feature_ablation_candidate_grid.csv'))==4334
check('sensitivity_limitations','','4,334','results/sensitivity/feature_ablation_candidate_grid.csv [rows]',4334,0)
p='results/benchmark/selected_label_free.csv';a=read(p)
for method,printed in [('kmeans','0.597'),('ward','0.575'),('dbscan','0.509'),('classix','0.508')]:
    check('benchmark_results','',printed,p+f' [{method} nine-dataset mean ARI]',mean(float(r['ari_mean']) for r in a if r['method']==method))
for dataset,method,printed in [('aggregation','dbscan','0.910'),('compound','dbscan','0.826'),('iris','classix','0.568'),('iris','kmeans','0.568'),('jain','classix','1.000'),('pathbased','classix','0.497'),('r15','ward','0.804'),('seeds','kmeans','0.481'),('spiral','dbscan','1.000'),('wine','kmeans','0.897')]:
    v=next(r for r in a if r['dataset']==dataset and r['method']==method)
    check('benchmark_results','',printed,p+f' [{dataset}/{method} ARI]',float(v['ari_mean']))
for method,printed in [('classix','0.011'),('kmeans','0.064'),('dbscan','0.003'),('ward','0.004')]:
    actual=median(float(r['runtime_seconds_mean']) for r in a if r['method']==method)
    assert printed not in (ROOT/'dissertation/overleaf/sections/benchmark_results.tex').read_text()
    rows.append(['baseline benchmark_results.tex:28',printed,p+f' [{method} median runtime]',f'{actual:.12g}','Withdrawn','Original claim disagrees; removed without replacing saved results or rerunning'])
header='# Numerical audit\n\nExplicit saved-output claim checks. Each row compares a manuscript literal with a specific saved-output selector or aggregation; no experiment is rerun. Locations can contain several occurrences and still require contextual reviewer confirmation. Additional non-literal and protocol checks are documented in numerical_scope.md.\n\n| Claim/location | Manuscript value | Source artifact | Artifact value | Match? | Action |\n| --- | --- | --- | --- | --- | --- |\n'
(ROOT/'revision/numerical_audit.md').write_text(header+'\n'.join('| '+' | '.join(row)+' |' for row in rows)+'\n\n## Complementary scope\n\nSee numerical_scope.md for protocol, source-data, profile and non-literal checks; consistency_check.json independently verifies labels, transitions, addressability and the empirical freeze. Four unsupported baseline runtime statements are explicitly withdrawn above.\n')
print(f'{len(rows)} located claim checks; {sum(r[4]=="Yes" for r in rows)} passed; paired cohort/features identical.')
assert all(r[4] in {'Yes','Withdrawn'} for r in rows)

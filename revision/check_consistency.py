"""Read-only saved-result consistency and empirical-freeze audit."""
import csv,json,hashlib,subprocess,math,itertools
from collections import Counter
from pathlib import Path
from statistics import mean,median
ROOT=Path(__file__).resolve().parents[1]
def read(p):return list(csv.DictReader((ROOT/p).open()))
checks=[]
def record(name,condition,detail):
    checks.append({'check':name,'pass':bool(condition),'detail':detail})
    assert condition,(name,detail)
base='6be20f7'
old=json.loads(subprocess.check_output(['git','show',base+':REPOSITORY_MANIFEST.json'],cwd=ROOT,text=True))
for f in old['files']:
    if f['path'].startswith(('data/','protocol/','results/')) and f['path']!='results/retailrocket/classix_provenance.json':
        record('frozen '+f['path'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256'],'Baseline SHA256 unchanged')
oldprov=json.loads(subprocess.check_output(['git','show',base+':results/retailrocket/classix_provenance.json'],cwd=ROOT,text=True))
prov=json.loads((ROOT/'results/retailrocket/classix_provenance.json').read_text())
lab=read('results/retailrocket/selected_labels.csv');sel=read('results/retailrocket/selected_configurations.csv')
for rep in ['compact','rich']:
    for key in ['native_public_attributes','config','scaler','n_samples','n_features']:
        record(f'{rep} provenance immutable {key}',oldprov[rep][key]==prov[rep][key],'Only derived correspondence corrected')
    trace=prov[rep]['customer_trace'];lookup={int(r['visitorid']):int(r['label']) for r in lab if r['representation']==rep and r['method']=='classix' and r['selection']=='deployment_acceptable'}
    record(rep+' trace exact labels',len(lookup)==11719 and all(lookup[r['customer_id']]==r['final_cluster'] for r in trace),'All customer labels match selected_labels.csv')
    for g in prov[rep]['groups']:
        record(f'{rep} group {g["aggregation_group"]}',g['representative_row_index'] in g['member_row_indices'] and all(trace[i]['final_cluster']==g['final_cluster'] and trace[i]['aggregation_group']==g['aggregation_group'] for i in g['member_row_indices']),'Representative membership and cluster consistency')
for r in sel:
    a=[x for x in lab if all(x[k]==r[k] for k in ['representation','method','selection'])]
    counts=Counter(int(x['label']) for x in a)
    record(r['candidate_id']+'/'+r['representation']+'/'+r['selection'],dict(counts)=={int(k):v for k,v in json.loads(r['cluster_sizes']).items()} and len(a)==11719,'Saved label counts equal selected configuration')
def scores(x,y):
    n=len(x);joint=Counter(zip(x,y));cx=Counter(x);cy=Counter(y)
    c2=lambda v:v*(v-1)/2
    ij=sum(c2(v) for v in joint.values());a=sum(c2(v) for v in cx.values());b=sum(c2(v) for v in cy.values());expected=a*b/c2(n)
    ari=(ij-expected)/((a+b)/2-expected)
    entropy=lambda c:-sum((v/n)*math.log(v/n) for v in c.values())
    h1,h2=entropy(cx),entropy(cy);mi=sum((v/n)*math.log(v*n/(cx[i]*cy[j])) for (i,j),v in joint.items())
    return ari,2*mi/(h1+h2),h1+h2-2*mi
for method in ['kmeans','classix']:
    maps=[{int(r['visitorid']):int(r['label']) for r in lab if r['method']==method and r['representation']==rep and r['selection']=='deployment_acceptable'} for rep in ['compact','rich']]
    ids=sorted(maps[0]);values=scores(*[[m[i] for i in ids] for m in maps])
    row=next(r for r in read('results/retailrocket/paired_partition_comparison.csv') if r['method']==method and r['comparison']=='independent_deployment_selection')
    record(method+' independent ARI/NMI/VI',all(abs(v-float(row[k]))<1e-12 for k,v in zip(['ari','nmi','vi'],values)),dict(zip(['ARI','NMI','VI'],values)))
    transitions=read('results/retailrocket/cluster_transition_matrix.csv');actual=Counter(zip(*[[m[i] for i in ids] for m in maps]));reported={(int(r['source_cluster']),int(r['target_cluster_original'])):int(r['n_customers']) for r in transitions if r['method']==method}
    record(method+' transitions',all(actual[k]==v for k,v in reported.items()) and sum(reported.values())==11719,'Independently recounted transitions')
address=read('results/retailrocket/addressability_audit.csv')
for r in address:
    effects=json.loads(r['feature_effects_iqr']);n=sum(abs(float(v))>=0.5 for v in effects.values() if v is not None)
    expected=int(r['non_noise_cluster_size'])>=50 and float(r['non_noise_cluster_share'])>=0.01 and float(r['category_coverage_rate'])>=0.8 and 2<=n<=4
    record('addressability '+r['representation']+'/'+r['split_or_config']+'/'+r['cluster_id'],expected==(r['addressable']=='True') and n==int(r['distinguishable_condition_count']),'Recomputed size/share/coverage/effect gates')
for rep,config,num in [('compact','selected_classix',0),('rich','selected_classix',0),('compact','selected_kmeans',0),('rich','selected_kmeans',1)]:
    record(rep+'/'+config+' addressability count',sum(r['addressable']=='True' for r in address if r['representation']==rep and r['split_or_config']==config)==num,num)
profiles=read('results/retailrocket/cluster_profiles.csv')
for size,method,feature,expected in [(166,'kmeans','total_events',338.5),(166,'kmeans','session_count_30m',28),(166,'kmeans','distinct_top_categories',12),(1156,'kmeans','purchase_recency_days',127.4),(33,'classix','total_events',869),(33,'classix','session_count_30m',36),(33,'classix','distinct_top_categories',14)]:
    r=next(r for r in profiles if r['representation']=='rich' and r['method']==method and r['selection']=='deployment_acceptable' and int(r['n_customers'])==size and r['feature']==feature)
    record(f'profile {method}/{size}/{feature}',abs(float(r['median'])-expected)<0.051,{'reported':expected,'artifact':float(r['median'])})
raw=json.loads((ROOT/'revision/raw_reproduction_check.json').read_text())
record('raw reproduction',all(r['match'] for r in raw['feature_comparisons']) and raw['purchaser_timestamps_match'],'Four input hashes and all distributed customer tables independently rebuilt')
bench=read('results/benchmark/selected_label_free.csv');ranks={m:[] for m in ['classix','kmeans','dbscan','ward']}
for ds in sorted({r['dataset'] for r in bench}):
    a=[r for r in bench if r['dataset']==ds];vals=[float(r['ari_mean']) for r in a]
    for r,v in zip(a,vals):ranks[r['method']].append(1+sum(x>v for x in vals)+(sum(x==v for x in vals)-1)/2)
for m,want in [('classix',2.44),('ward',2.44),('kmeans',2.39),('dbscan',2.72)]:record(m+' benchmark average rank',abs(mean(ranks[m])-want)<=0.005,mean(ranks[m]))
(ROOT/'revision/consistency_check.json').write_text(json.dumps({'passed':len(checks),'checks':checks},indent=2)+'\n')
print(len(checks),'consistency checks passed; independent ARI/NMI/VI and freeze verified.')

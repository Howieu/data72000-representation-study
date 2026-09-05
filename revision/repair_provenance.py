"""Repair only exported row alignment from saved native arrays; no model fitting."""
import csv,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.provenance_alignment import align_groups
p=ROOT/'results/retailrocket/classix_provenance.json';data=json.loads(p.read_text())
for rep,v in data.items():
    a=v['native_public_attributes'];labels=a['labels_'];reps=a['groupCenters_']
    groups=align_groups(a['groups_'],a['inverse_ind'],reps,labels)
    ids=[int(r['visitorid']) for r in csv.DictReader((ROOT/f'data/derived/{rep}_features.csv').open())]
    sizes=Counter(labels);members={gid:[] for gid in range(len(reps))}
    for i,gid in enumerate(groups):members[gid].append(i)
    v['groups']=[{'aggregation_group':gid,'representative_row_index':int(reps[gid]),'representative_customer_id':ids[reps[gid]],'member_row_indices':m,'member_customer_ids':[ids[i] for i in m],'group_size':len(m),'final_cluster':labels[m[0]],'final_cluster_size':sizes[labels[m[0]]]} for gid,m in members.items()]
    v['merge_relations']=[{'final_cluster':cluster,'aggregation_groups':sorted({g for g,y in zip(groups,labels) if y==cluster}),'cluster_size':size,'relation_status':'reconstructed_from_public_assignments'} for cluster,size in sorted(sizes.items())]
    v['customer_trace']=[{'row_index':i,'customer_id':ids[i],'aggregation_group':groups[i],'representative_row_index':reps[groups[i]],'final_cluster':labels[i],'final_cluster_size':sizes[labels[i]]} for i in range(len(ids))]
    v['schema_version']='1.0.1'
    v['provenance_limits']['group_row_order']='native groups_ uses sorted rows; exported groups and customer_trace use inverse_ind to restore input order'
p.write_text(json.dumps(data,indent=2,ensure_ascii=False))
print('Corrected exported provenance only; native arrays, labels, settings and scalers retained.')

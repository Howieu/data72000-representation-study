"""Small deterministic checks of mathematical helpers, not customer experiments."""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from src.mathematics.classix_math import projection_pruning_check,pca_score_perturbation_bound
x=np.array([[0.,0.],[1.,0.],[0.5,3.],[2.,0.]])
r=projection_pruning_check(x,[1.,0.],1.)
assert r['exact'] and r['false_negative_count']==0 and r['false_positive_count']>0
# Small covariance rotation: verify the derived score bound on explicitly perturbed points.
x=np.array([[-3.,0.],[-1.,0.2],[1.,-0.2],[3.,0.]])
hat=x+np.array([[0.,0.01],[0.01,0.],[0.,-0.01],[-0.01,0.]])
x-=x.mean(axis=0);hat-=hat.mean(axis=0)
s=x.T@x/len(x);hs=hat.T@hat/len(hat)
w,u=np.linalg.eigh(s);_,hu=np.linalg.eigh(hs);u=u[:,-1];hu=hu[:,-1]
if u@hu<0:hu=-hu
bound=pca_score_perturbation_bound(np.linalg.norm(x,axis=1).max(),np.linalg.norm(hat-x,axis=1).max(),np.linalg.norm(hs-s,ord=2),w[-1]-w[-2])
observed=float(np.max(np.abs(hat@hu-x@u)))
assert observed<=bound
(ROOT/'revision/mathematical_check.json').write_text(json.dumps({'projection_no_false_negatives':True,'projection_false_positives_possible':True,'score_bound':float(bound),'observed_score_movement':observed,'scope':'Deterministic helper checks only; does not certify any customer fit.'},indent=2)+'\n')
print('Projection-boundary and covariance/score-bound checks passed.')

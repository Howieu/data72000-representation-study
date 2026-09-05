"""Optional read-only data reproduction; never writes derived tables or results."""
import argparse, csv, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pandas as pd
from src.representation.features import load_events,load_category_history,attach_categories_asof,build_feature_tables
parser=argparse.ArgumentParser();parser.add_argument('--raw-dir',type=Path,required=True);args=parser.parse_args()
verified=[]
for r in csv.DictReader((ROOT/'data/manifests/input_hashes.csv').open()):
 p=args.raw_dir/r['file'];h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 assert h.hexdigest()==r['sha256'],p
 verified.append({'file':r['file'],'sha256':h.hexdigest()})
print('Four raw hashes verified.',flush=True)
events=load_events(args.raw_dir/'events.csv')
history=load_category_history([args.raw_dir/'item_properties_part1.csv',args.raw_dir/'item_properties_part2.csv'])
enriched,joins=attach_categories_asof(events,history,args.raw_dir/'category_tree.csv')
compact,rich,audit,metadata=build_feature_tables(enriched)
checks=[]
for name,frame in [('compact_features.csv',compact),('rich_features.csv',rich),('category_coverage_audit.csv',audit)]:
 saved=pd.read_csv(ROOT/'data/derived'/name)
 pd.testing.assert_frame_equal(frame.reset_index(drop=True),saved,check_dtype=False,check_exact=False,rtol=1e-12,atol=1e-12)
 checks.append({'file':name,'rows':len(frame),'columns':len(frame.columns),'match':True})
purch=events[events.visitorid.isin(rich.visitorid)].sort_values(['visitorid','timestamp','raw_row_id'],kind='mergesort')[['visitorid','timestamp']].reset_index(drop=True)
pd.testing.assert_frame_equal(purch,pd.read_csv(ROOT/'data/derived/purchaser_event_timestamps.csv'),check_dtype=False)
assert joins['known_category_event_rows']==2099173
assert round(100*joins['event_category_coverage'],2)==76.16
assert len(purch)==230678
out={'command':'python revision/check_raw_reproduction.py --raw-dir <original RetailRocket directory>','raw_files':verified,'category_join':joins,'feature_comparisons':checks,'purchaser_timestamp_rows':len(purch),'purchaser_timestamps_match':True,'metadata':metadata,'tolerance':{'rtol':1e-12,'atol':1e-12},'experimental_fits_run':0,'data_or_results_written':False,'pandas_version':pd.__version__}
(ROOT/'revision/raw_reproduction_check.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
print('All feature, coverage and purchaser-timestamp tables reproduced; no data/results written.',flush=True)

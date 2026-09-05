import json,unittest
from pathlib import Path
from src.provenance_alignment import align_groups

class ProvenanceAlignmentTests(unittest.TestCase):
    def test_nonidentity_permutation(self):
        self.assertEqual(align_groups([0,0,1],[2,0,1],[1,0],[8,7,7]),[1,0,0])
    def test_rejects_group_crossing_labels(self):
        with self.assertRaisesRegex(ValueError,'crosses'):
            align_groups([0,0,1],[2,0,1],[1,0],[8,7,8])
    def test_rejects_wrong_representative(self):
        with self.assertRaisesRegex(ValueError,'Representative'):
            align_groups([0,0,1],[2,0,1],[0,1],[8,7,7])
    def test_rejects_bad_permutation(self):
        with self.assertRaisesRegex(ValueError,'permutation'):
            align_groups([0,0,1],[0,0,2],[0,2],[7,7,8])
    def test_saved_trace_consistency(self):
        root=Path(__file__).resolve().parents[1]
        data=json.loads((root/'results/retailrocket/classix_provenance.json').read_text())
        for v in data.values():
            a=v['native_public_attributes']
            groups=align_groups(a['groups_'],a['inverse_ind'],a['groupCenters_'],a['labels_'])
            self.assertEqual(groups,[r['aggregation_group'] for r in v['customer_trace']])
            for g in v['groups']:
                self.assertIn(g['representative_row_index'],g['member_row_indices'])
                self.assertEqual({a['labels_'][i] for i in g['member_row_indices']},{g['final_cluster']})
if __name__=='__main__':unittest.main()

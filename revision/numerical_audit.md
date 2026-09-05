# Numerical audit

Explicit saved-output claim checks. Each row compares a manuscript literal with a specific saved-output selector or aggregation; no experiment is rerun. Locations can contain several occurrences and still require contextual reviewer confirmation. Additional non-literal and protocol checks are documented in numerical_scope.md.

| Claim/location | Manuscript value | Source artifact | Artifact value | Match? | Action |
| --- | --- | --- | --- | --- | --- |
| paired_results.tex:13,21 () | 0.595 | results/retailrocket/selected_configurations.csv [compact/classix/silhouette] | 0.594745572175 | Yes | Retain |
| paired_results.tex:21 () | 1.057 | results/retailrocket/selected_configurations.csv [compact/classix/davies_bouldin] | 1.05722645332 | Yes | Retain |
| paired_results.tex:21 () | 4285.5 | results/retailrocket/selected_configurations.csv [compact/classix/calinski_harabasz] | 4285.46660525 | Yes | Retain |
| paired_results.tex:15,21 () | 0.560 | results/retailrocket/selected_configurations.csv [compact/kmeans/silhouette] | 0.559514302869 | Yes | Retain |
| paired_results.tex:21 () | 0.775 | results/retailrocket/selected_configurations.csv [compact/kmeans/davies_bouldin] | 0.774552326694 | Yes | Retain |
| paired_results.tex:21 () | 10459.1 | results/retailrocket/selected_configurations.csv [compact/kmeans/calinski_harabasz] | 10459.0755692 | Yes | Retain |
| paired_results.tex:14,21 () | 0.291 | results/retailrocket/selected_configurations.csv [rich/classix/silhouette] | 0.290913633679 | Yes | Retain |
| paired_results.tex:21 () | 0.859 | results/retailrocket/selected_configurations.csv [rich/classix/davies_bouldin] | 0.859209473469 | Yes | Retain |
| paired_results.tex:21 () | 1516.9 | results/retailrocket/selected_configurations.csv [rich/classix/calinski_harabasz] | 1516.91990257 | Yes | Retain |
| paired_results.tex:16,21 () | 0.351 | results/retailrocket/selected_configurations.csv [rich/kmeans/silhouette] | 0.351089398194 | Yes | Retain |
| paired_results.tex:21 () | 1.040 | results/retailrocket/selected_configurations.csv [rich/kmeans/davies_bouldin] | 1.04037533734 | Yes | Retain |
| paired_results.tex:21 () | 3923.4 | results/retailrocket/selected_configurations.csv [rich/kmeans/calinski_harabasz] | 3923.36192165 | Yes | Retain |
| paired_results.tex:13,40 () | 0.985 | results/retailrocket/resampling_stability.csv [mean compact/classix, n=10] | 0.98507915854 | Yes | Retain |
| paired_results.tex:14,40 () | 0.965 | results/retailrocket/resampling_stability.csv [mean rich/classix, n=10] | 0.964659631977 | Yes | Retain |
| paired_results.tex:15,40 () | 0.988 | results/retailrocket/resampling_stability.csv [mean compact/kmeans, n=10] | 0.988463900073 | Yes | Retain |
| paired_results.tex:16,40 () | 0.995 | results/retailrocket/resampling_stability.csv [mean rich/kmeans, n=10] | 0.994769066232 | Yes | Retain |
| explanation_results.tex:7 () | 0.9448 | results/retailrocket/exkmc_oos_fidelity.csv [mean compact, leaves=4, n=5] | 0.944795221843 | Yes | Retain |
| explanation_results.tex:7 () | 0.9650 | results/retailrocket/exkmc_oos_fidelity.csv [mean rich, leaves=4, n=5] | 0.965017064846 | Yes | Retain |
| explanation_results.tex:18 () | 0.9924 | results/retailrocket/exkmc_oos_fidelity.csv [mean compact, leaves=16, n=5] | 0.992406143345 | Yes | Retain |
| explanation_results.tex:18 () | 0.9747 | results/retailrocket/exkmc_oos_fidelity.csv [mean rich, leaves=16, n=5] | 0.974744027304 | Yes | Retain |
| sensitivity_limitations.tex:27 () | 0.976 | results/sensitivity/session_window_sensitivity.csv [kmeans/15 minutes] | 0.975630503338 | Yes | Retain |
| sensitivity_limitations.tex:27 () | 0.971 | results/sensitivity/session_window_sensitivity.csv [classix/15 minutes] | 0.970670444763 | Yes | Retain |
| sensitivity_limitations.tex:25,27 () | 0.985 | results/sensitivity/session_window_sensitivity.csv [kmeans/60 minutes] | 0.984955629659 | Yes | Retain |
| sensitivity_limitations.tex:27 () | 0.959 | results/sensitivity/session_window_sensitivity.csv [classix/60 minutes] | 0.958866498148 | Yes | Retain |
| sensitivity_limitations.tex:7 () | 0.516 | results/sensitivity/feature_ablation.csv [('kmeans', 'distinct_top_categories')] | 0.515926527077 | Yes | Retain |
| sensitivity_limitations.tex:7 () | 0.517 | results/sensitivity/feature_ablation.csv [('kmeans', 'top_category_share')] | 0.517026393173 | Yes | Retain |
| sensitivity_limitations.tex:7 () | 0.189 | results/sensitivity/feature_ablation.csv [('classix', 'distinct_top_categories')] | 0.188998257198 | Yes | Retain |
| sensitivity_limitations.tex:7 () | 0.238 | results/sensitivity/feature_ablation.csv [('classix', 'top_category_share')] | 0.237674278367 | Yes | Retain |
| data_representation.tex:3,9,48 () | 11,719 | data/derived/{compact,rich}_features.csv [row count; same IDs and compact values] | 11719 | Yes | Retain |
| paired_results.tex:3,32 () | 0.014 | results/retailrocket/paired_partition_comparison.csv [kmeans/ari] | 0.0139744627294 | Yes | Retain |
| paired_results.tex:32 () | 0.089 | results/retailrocket/paired_partition_comparison.csv [kmeans/nmi] | 0.0893862339027 | Yes | Retain |
| paired_results.tex:32 () | 1.691 | results/retailrocket/paired_partition_comparison.csv [kmeans/vi] | 1.69080466585 | Yes | Retain |
| paired_results.tex:3 () | 0.068 | results/retailrocket/paired_partition_comparison.csv [classix/ari] | 0.0681249825577 | Yes | Retain |
| paired_results.tex:32 () | 0.054 | results/retailrocket/paired_partition_comparison.csv [classix/nmi] | 0.0537937937822 | Yes | Retain |
| paired_results.tex:32 () | 0.693 | results/retailrocket/paired_partition_comparison.csv [classix/vi] | 0.692901318621 | Yes | Retain |
| paired_results.tex:32 () | 0.012 | results/retailrocket/paired_partition_comparison.csv [fixed K minimum] | 0.0120076080807 | Yes | Retain |
| paired_results.tex:32 () | 0.113 | results/retailrocket/paired_partition_comparison.csv [fixed K maximum] | 0.112549006298 | Yes | Retain |
| paired_results.tex:32,40 () | 41 | results/retailrocket/paired_partition_comparison.csv [CLASSIX matched acceptable settings] | 41 | Yes | Retain |
| paired_results.tex:32 () | -0.051 | results/retailrocket/paired_partition_comparison.csv [CLASSIX matched acceptable settings] | -0.0509182114975 | Yes | Retain |
| paired_results.tex:32 () | 0.392 | results/retailrocket/paired_partition_comparison.csv [CLASSIX matched acceptable settings] | 0.392465788577 | Yes | Retain |
| paired_results.tex:32 () | -0.023 | results/retailrocket/paired_partition_comparison.csv [CLASSIX matched acceptable settings] | -0.0225711965167 | Yes | Retain |
| paired_results.tex:32 () | 54.61 | results/retailrocket/cluster_transition_matrix.csv [kmeans migrated percent] | 54.6121682737 | Yes | Retain |
| paired_results.tex:32 () | 18.66 | results/retailrocket/cluster_transition_matrix.csv [classix migrated percent] | 18.6620018773 | Yes | Retain |
| paired_results.tex:30 () | 11,698 | results/retailrocket/selected_configurations.csv [compact/classix/unconstrained_silhouette] largest size | 11698 | Yes | Retain |
| paired_results.tex:30 () | 0.899 | results/retailrocket/selected_configurations.csv [compact/classix/unconstrained_silhouette] silhouette | 0.899490070629 | Yes | Retain |
| paired_results.tex:36 () | 1,063 | results/retailrocket/selected_configurations.csv [compact/classix/deployment_acceptable] cluster size | 1063 | Yes | Retain |
| paired_results.tex:36 () | 10,656 | results/retailrocket/selected_configurations.csv [compact/classix/deployment_acceptable] cluster size | 10656 | Yes | Retain |
| paired_results.tex:13 () | 0.909 | results/retailrocket/selected_configurations.csv [compact/classix/deployment_acceptable] largest share | 0.909292601758 | Yes | Retain |
| paired_results.tex:30 () | 11,593 | results/retailrocket/selected_configurations.csv [compact/kmeans/unconstrained_silhouette] largest size | 11593 | Yes | Retain |
| paired_results.tex:30 () | 0.850 | results/retailrocket/selected_configurations.csv [compact/kmeans/unconstrained_silhouette] silhouette | 0.850142564589 | Yes | Retain |
| paired_results.tex:34 () | 1,344 | results/retailrocket/selected_configurations.csv [compact/kmeans/deployment_acceptable] cluster size | 1344 | Yes | Retain |
| paired_results.tex:34 () | 7,784 | results/retailrocket/selected_configurations.csv [compact/kmeans/deployment_acceptable] cluster size | 7784 | Yes | Retain |
| paired_results.tex:34 () | 97 | results/retailrocket/selected_configurations.csv [compact/kmeans/deployment_acceptable] cluster size | 97 | Yes | Retain |
| paired_results.tex:34 () | 2,494 | results/retailrocket/selected_configurations.csv [compact/kmeans/deployment_acceptable] cluster size | 2494 | Yes | Retain |
| paired_results.tex:15 () | 0.664 | results/retailrocket/selected_configurations.csv [compact/kmeans/deployment_acceptable] largest share | 0.664220496629 | Yes | Retain |
| paired_results.tex:30 () | 11,716 | results/retailrocket/selected_configurations.csv [rich/classix/unconstrained_silhouette] largest size | 11716 | Yes | Retain |
| paired_results.tex:30 () | 0.792 | results/retailrocket/selected_configurations.csv [rich/classix/unconstrained_silhouette] silhouette | 0.791901207237 | Yes | Retain |
| paired_results.tex:3,14,36 () | 218 | results/retailrocket/selected_configurations.csv [rich/classix/deployment_acceptable] cluster size | 218 | Yes | Retain |
| paired_results.tex:34,36 () | 33 | results/retailrocket/selected_configurations.csv [rich/classix/deployment_acceptable] cluster size | 33 | Yes | Retain |
| paired_results.tex:36 () | 1,137 | results/retailrocket/selected_configurations.csv [rich/classix/deployment_acceptable] cluster size | 1137 | Yes | Retain |
| paired_results.tex:36 () | 10,331 | results/retailrocket/selected_configurations.csv [rich/classix/deployment_acceptable] cluster size | 10331 | Yes | Retain |
| paired_results.tex:14 () | 0.898 | results/retailrocket/selected_configurations.csv [rich/classix/deployment_acceptable] largest share | 0.898269715677 | Yes | Retain |
| paired_results.tex:34 () | 6,790 | results/retailrocket/selected_configurations.csv [rich/kmeans/deployment_acceptable] cluster size | 6790 | Yes | Retain |
| paired_results.tex:34 () | 3,607 | results/retailrocket/selected_configurations.csv [rich/kmeans/deployment_acceptable] cluster size | 3607 | Yes | Retain |
| paired_results.tex:34 () | 166 | results/retailrocket/selected_configurations.csv [rich/kmeans/deployment_acceptable] cluster size | 166 | Yes | Retain |
| paired_results.tex:34 () | 1,156 | results/retailrocket/selected_configurations.csv [rich/kmeans/deployment_acceptable] cluster size | 1156 | Yes | Retain |
| paired_results.tex:16 () | 0.579 | results/retailrocket/selected_configurations.csv [rich/kmeans/deployment_acceptable] largest share | 0.579400972779 | Yes | Retain |
| explanation_results.tex:5 () | 131 | results/retailrocket/classix_provenance.json [compact group count] | 131 | Yes | Retain |
| explanation_results.tex:5 () | 559 | results/retailrocket/classix_provenance.json [rich group count] | 559 | Yes | Retain |
| explanation_results.tex:7 () | 0.9466 | results/retailrocket/exkmc_oos_fidelity.csv [compact/4 mean train_fidelity] | 0.94656 | Yes | Retain |
| explanation_results.tex:7 () | 0.9639 | results/retailrocket/exkmc_oos_fidelity.csv [rich/4 mean train_fidelity] | 0.963925333333 | Yes | Retain |
| explanation_results.tex:7 () | 2.25 | results/retailrocket/exkmc_oos_fidelity.csv [compact/4 mean mean_conditions_per_rule] | 2.25 | Yes | Retain |
| explanation_results.tex:7 () | 2.25 | results/retailrocket/exkmc_oos_fidelity.csv [rich/4 mean mean_conditions_per_rule] | 2.25 | Yes | Retain |
| explanation_results.tex:18 () | 6.6 | results/retailrocket/exkmc_oos_fidelity.csv [compact/16 mean max_depth] | 6.6 | Yes | Retain |
| explanation_results.tex:18 () | 6.4 | results/retailrocket/exkmc_oos_fidelity.csv [rich/16 mean max_depth] | 6.4 | Yes | Retain |
| explanation_results.tex:18 () | 4.84 | results/retailrocket/exkmc_oos_fidelity.csv [compact/16 mean mean_conditions_per_rule] | 4.8375 | Yes | Retain |
| explanation_results.tex:18 () | 4.74 | results/retailrocket/exkmc_oos_fidelity.csv [rich/16 mean mean_conditions_per_rule] | 4.7375 | Yes | Retain |
| explanation_results.tex:7 () | 0.9416 | results/retailrocket/exkmc_oos_fidelity.csv [compact/4 minimum] | 0.941552901024 | Yes | Retain |
| explanation_results.tex:7 () | 0.9480 | results/retailrocket/exkmc_oos_fidelity.csv [compact/4 maximum] | 0.94795221843 | Yes | Retain |
| explanation_results.tex:7 () | 0.9599 | results/retailrocket/exkmc_oos_fidelity.csv [rich/4 minimum] | 0.959897610922 | Yes | Retain |
| explanation_results.tex:7 () | 0.9697 | results/retailrocket/exkmc_oos_fidelity.csv [rich/4 maximum] | 0.969709897611 | Yes | Retain |
| explanation_results.tex:18 () | 0.9985 | results/retailrocket/exkmc_train_selected_oos_fidelity.csv [compact selected-K mean test fidelity] | 0.998549488055 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 91.32 | results/sensitivity/pca_sensitivity.csv [variance percent] | 91.319690628 | Yes | Retain |
| sensitivity_limitations.tex:9,25 () | 0.995 | results/sensitivity/pca_sensitivity.csv [kmeans/reference_ari] | 0.995064988466 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 0.390 | results/sensitivity/pca_sensitivity.csv [kmeans/silhouette] | 0.390473427322 | Yes | Retain |
| sensitivity_limitations.tex:9,25 () | 0.995 | results/sensitivity/pca_sensitivity.csv [kmeans/resampling_ari_mean] | 0.995365764064 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 91.32 | results/sensitivity/pca_sensitivity.csv [variance percent] | 91.319690628 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 0.920 | results/sensitivity/pca_sensitivity.csv [classix/reference_ari] | 0.920127834065 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 0.304 | results/sensitivity/pca_sensitivity.csv [classix/silhouette] | 0.304362395169 | Yes | Retain |
| sensitivity_limitations.tex:9 () | 0.987 | results/sensitivity/pca_sensitivity.csv [classix/resampling_ari_mean] | 0.987224008794 | Yes | Retain |
| sensitivity_limitations.tex:25 () | 0.999 | results/sensitivity/classix_perturbation_stability.csv [compact/0.01 mean] | 0.99891907769 | Yes | Retain |
| sensitivity_limitations.tex:25 () | 0.996 | results/sensitivity/classix_perturbation_stability.csv [compact/0.01 minimum] | 0.995524856527 | Yes | Retain |
| sensitivity_limitations.tex:9,25 () | 0.995 | results/sensitivity/classix_perturbation_stability.csv [rich/0.001 mean] | 0.995194305996 | Yes | Retain |
| sensitivity_limitations.tex:25,27 () | 0.985 | results/sensitivity/classix_perturbation_stability.csv [rich/0.001 minimum] | 0.984906515607 | Yes | Retain |
| sensitivity_limitations.tex:25,27 () | 0.985 | results/sensitivity/classix_perturbation_stability.csv [rich/0.01 mean] | 0.985034153982 | Yes | Retain |
| sensitivity_limitations.tex:25 () | 0.962 | results/sensitivity/classix_perturbation_stability.csv [rich/0.01 minimum] | 0.96153647302 | Yes | Retain |
| sensitivity_limitations.tex:31 () | 0.017 | results/sensitivity/permutation_dimension_control.csv [K Means nine dimensions ARI] | 0.0168124394206 | Yes | Retain |
| sensitivity_limitations.tex:31 () | 0.127 | results/sensitivity/permutation_dimension_control.csv [K Means nine dimensions silhouette] | 0.127462312508 | Yes | Retain |
| sensitivity_limitations.tex:18 () | 0.153 | results/sensitivity/feature_ablation_selected.csv [('classix', 'drop_feature_distinct_top_categories')/ARI vs rich] | 0.153292728989 | Yes | Retain |
| sensitivity_limitations.tex:18 () | 0.728 | results/sensitivity/feature_ablation_selected.csv [('kmeans', 'drop_feature_distinct_top_categories')/ARI vs rich] | 0.728363714489 | Yes | Retain |
| sensitivity_limitations.tex:18 () | 0.126 | results/sensitivity/feature_ablation_selected.csv [('classix', 'drop_block_category_behaviour')/ARI vs rich] | 0.126412621639 | Yes | Retain |
| sensitivity_limitations.tex:18 () | 0.729 | results/sensitivity/feature_ablation_selected.csv [('kmeans', 'drop_block_category_behaviour')/ARI vs rich] | 0.72864408643 | Yes | Retain |
| sensitivity_limitations.tex:18 () | 4,334 | results/sensitivity/feature_ablation_candidate_grid.csv [rows] | 4334 | Yes | Retain |
| benchmark_results.tex:5 () | 0.597 | results/benchmark/selected_label_free.csv [kmeans nine-dataset mean ARI] | 0.596708548454 | Yes | Retain |
| benchmark_results.tex:5 () | 0.575 | results/benchmark/selected_label_free.csv [ward nine-dataset mean ARI] | 0.575394452657 | Yes | Retain |
| benchmark_results.tex:5 () | 0.509 | results/benchmark/selected_label_free.csv [dbscan nine-dataset mean ARI] | 0.508966830048 | Yes | Retain |
| benchmark_results.tex:5 () | 0.508 | results/benchmark/selected_label_free.csv [classix nine-dataset mean ARI] | 0.508182683874 | Yes | Retain |
| benchmark_results.tex:15 () | 0.910 | results/benchmark/selected_label_free.csv [aggregation/dbscan ARI] | 0.909722207674 | Yes | Retain |
| benchmark_results.tex:16 () | 0.826 | results/benchmark/selected_label_free.csv [compound/dbscan ARI] | 0.825526572411 | Yes | Retain |
| benchmark_results.tex:17 () | 0.568 | results/benchmark/selected_label_free.csv [iris/classix ARI] | 0.568115942029 | Yes | Retain |
| benchmark_results.tex:17 () | 0.568 | results/benchmark/selected_label_free.csv [iris/kmeans ARI] | 0.568115942029 | Yes | Retain |
| benchmark_results.tex:18,22 () | 1.000 | results/benchmark/selected_label_free.csv [jain/classix ARI] | 1 | Yes | Retain |
| benchmark_results.tex:19 () | 0.497 | results/benchmark/selected_label_free.csv [pathbased/classix ARI] | 0.496889876693 | Yes | Retain |
| benchmark_results.tex:20 () | 0.804 | results/benchmark/selected_label_free.csv [r15/ward ARI] | 0.804276675364 | Yes | Retain |
| benchmark_results.tex:21 () | 0.481 | results/benchmark/selected_label_free.csv [seeds/kmeans ARI] | 0.480527582212 | Yes | Retain |
| benchmark_results.tex:18,22 () | 1.000 | results/benchmark/selected_label_free.csv [spiral/dbscan ARI] | 1 | Yes | Retain |
| benchmark_results.tex:23 () | 0.897 | results/benchmark/selected_label_free.csv [wine/kmeans ARI] | 0.897494981509 | Yes | Retain |
| baseline benchmark_results.tex:28 | 0.011 | results/benchmark/selected_label_free.csv [classix median runtime] | 0.0063470005116 | Withdrawn | Original claim disagrees; removed without replacing saved results or rerunning |
| baseline benchmark_results.tex:28 | 0.064 | results/benchmark/selected_label_free.csv [kmeans median runtime] | 0.0204280667938 | Withdrawn | Original claim disagrees; removed without replacing saved results or rerunning |
| baseline benchmark_results.tex:28 | 0.003 | results/benchmark/selected_label_free.csv [dbscan median runtime] | 0.00105593749322 | Withdrawn | Original claim disagrees; removed without replacing saved results or rerunning |
| baseline benchmark_results.tex:28 | 0.004 | results/benchmark/selected_label_free.csv [ward median runtime] | 0.00153047899948 | Withdrawn | Original claim disagrees; removed without replacing saved results or rerunning |

## Complementary scope

See numerical_scope.md for protocol, source-data, profile and non-literal checks; consistency_check.json independently verifies labels, transitions, addressability and the empirical freeze. Four unsupported baseline runtime statements are explicitly withdrawn above.

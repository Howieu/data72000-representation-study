# Terminology audit

Definitions are checked in reading order through the active input graph. Early high-level mentions of PCA/leaf budget in research design are expanded at their operational use. ARI is explicitly a comparison of two fitted partitions, not ground-truth accuracy for RetailRocket.

| Term | Definition location | Meaning anchor | Resolution |
| --- | --- | --- | --- |
| representation | introduction.tex:7 | choice and construction | Defined in context; later use inherits this meaning |
| feature geometry | introduction.tex:7 | distances and neighbourhood | Defined in context; later use inherits this meaning |
| clusterability | introduction.tex:9 | structure suitable | Defined in context; later use inherits this meaning |
| silhouette | methods_mathematics.tex:28 | mean distance | Defined in context; later use inherits this meaning |
| Davies--Bouldin | methods_mathematics.tex:28 | worst ratio | Defined in context; later use inherits this meaning |
| Calinski--Harabasz | methods_mathematics.tex:28 | squared dispersion | Defined in context; later use inherits this meaning |
| ARI | methods_mathematics.tex:30 | agreement in whether pairs | Defined in context; later use inherits this meaning |
| NMI | methods_mathematics.tex:30 | shared label information | Defined in context; later use inherits this meaning |
| variation of information | methods_mathematics.tex:30 | conditional entropies | Defined in context; later use inherits this meaning |
| Hungarian matching | methods_mathematics.tex:30 | one-to-one relabelling | Defined in context; later use inherits this meaning |
| resampling stability | methods_mathematics.tex:34 | independent 80 per cent | Defined in context; later use inherits this meaning |
| provenance | introduction.tex:11 | recorded route | Defined in context; later use inherits this meaning |
| fidelity | literature_review.tex:42 | exact predictive agreement | Defined in context; later use inherits this meaning |
| leaf budget | methods_mathematics.tex:38 | caps the number | Defined in context; later use inherits this meaning |
| addressability | methods_mathematics.tex:40 | size, coverage | Defined in context; later use inherits this meaning |
| aggregation group | methods_mathematics.tex:20 | intermediate object | Defined in context; later use inherits this meaning |
| principal direction | methods_mathematics.tex:20 | maximum variance | Defined in context; later use inherits this meaning |
| eigengap | methods_mathematics.tex:77 | clearly the leading direction | Defined in context; later use inherits this meaning |
| perturbation | methods_mathematics.tex:77 | change of the numerical input | Defined in context; later use inherits this meaning |
| PCA | data_representation.tex:46 | orthogonal linear combinations | Defined in context; later use inherits this meaning |
| noise | methods_mathematics.tex:22 | absence from a retained cluster | Defined in context; later use inherits this meaning |
| density merging | methods_mathematics.tex:22 | intersection density | Defined in context; later use inherits this meaning |
| distance merging | methods_mathematics.tex:22 | connected groups | Defined in context; later use inherits this meaning |

## Mathematical symbols

Section 3.2.3 defines x_i, d, u, s_i, c, r, n and q. Section 3.2.4 defines S, lambda_1, lambda_2, gamma, Delta S, u/hat u, epsilon_x, B, b_s, g_s, g_o, g_w, g_r, g_m, b_r and b_m, with prose interpretations and exact-arithmetic scope. The merge search window is included in g_w. Changes to preprocessing belong in the processed perturbation bounds. Nearest-eligible-group and tie decisions remain additional conditions.

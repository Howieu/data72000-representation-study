"""Validate and align CLASSIX's sorted group IDs to original input rows."""


def align_groups(groups_sorted, inverse_ind, representatives, labels):
    """Return input-order group IDs, rejecting inconsistent provenance.

    CLASSIX 1.5.1 groups_ is in sorted order. inverse_ind maps input rows
    to sorted positions; groupCenters_ and labels_ already use input order.
    """
    n = len(labels)
    if len(groups_sorted) != n or sorted(inverse_ind) != list(range(n)):
        raise ValueError('Invalid CLASSIX group length or inverse permutation')
    groups = [int(groups_sorted[int(i)]) for i in inverse_ind]
    if sorted(set(groups)) != list(range(len(representatives))):
        raise ValueError('Group IDs do not match representatives')
    group_labels = {}
    for gid, label in zip(groups, labels):
        if gid in group_labels and group_labels[gid] != int(label):
            raise ValueError('An aggregation group crosses final cluster labels')
        group_labels[gid] = int(label)
    for gid, rep in enumerate(representatives):
        if not 0 <= int(rep) < n or groups[int(rep)] != gid:
            raise ValueError('Representative does not belong to its group')
    return groups

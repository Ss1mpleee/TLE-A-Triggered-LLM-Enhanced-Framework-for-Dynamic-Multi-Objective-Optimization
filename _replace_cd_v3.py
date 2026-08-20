# -*- coding: utf-8 -*-
"""
Fix the label-overlap bug: for each adjacent pair whose rank distance
is < 0.20, force the two labels to opposite anchors (one left, one
right).  Otherwise, use center.  This is the canonical Demšar 2006
label-collision fix.
"""
PATH = r"D:\新论文\实验\experiments\stats_ablation_crossllm.py"
with open(PATH, "r", encoding="utf-8") as f:
    src = f.read()

old_block = '''    # Labels under markers.  If two ranks are within 0.20 of each other,
    # shift one label left and one right (anchor-based placement).
    sorted_by_rank = sorted(zip(sorted_keys, ranks), key=lambda kr: kr[1])
    label_anchors = {}  # key -> (x, ha)
    for i, (key, rank) in enumerate(sorted_by_rank):
        ha = 'center'
        if i > 0:
            prev_key, prev_rank = sorted_by_rank[i - 1]
            if rank - prev_rank < 0.20:
                # Anchor: shift this one to the right
                ha = 'left'
        if i < len(sorted_by_rank) - 1:
            next_key, next_rank = sorted_by_rank[i + 1]
            if next_rank - rank < 0.20:
                # Anchor: shift this one to the left
                ha = 'right'
        label_anchors[key] = (rank, ha)'''

new_block = '''    # Labels under markers.  If two ranks are within 0.25 of each other,
    # force the two labels to opposite anchors (one left, one right).
    # Iterate in rank order; for each conflict pair, the lower-rank
    # marker goes RIGHT and the higher-rank marker goes LEFT.
    sorted_by_rank = sorted(zip(sorted_keys, ranks), key=lambda kr: kr[1])
    label_anchors = {}  # key -> ha ('left' | 'right' | 'center')
    for i, (key, rank) in enumerate(sorted_by_rank):
        # Default: center
        ha = 'center'
        # Check the pair to the right (next neighbor)
        if i < len(sorted_by_rank) - 1:
            next_key, next_rank = sorted_by_rank[i + 1]
            if next_rank - rank < 0.25:
                ha = 'right'  # shift this label to the right of its marker
                # And the next one must go left
                # (force the next iteration; but also set it now in case
                #  the next loop iteration doesn't reset)
                label_anchors.setdefault(next_key, 'left')
        # Check the pair to the left (prev neighbor): if previous went
        # right because we are close, we must go left
        if i > 0:
            prev_key, prev_rank = sorted_by_rank[i - 1]
            if rank - prev_rank < 0.25 and label_anchors.get(prev_key) == 'right':
                ha = 'left'
        label_anchors[key] = ha'''

if old_block in src:
    new_src = src.replace(old_block, new_block)
    with open(PATH, "w", encoding="utf-8") as f:
        f.write(new_src)
    print(f"[cd-fix3] replaced anchor logic")
else:
    print("[cd-fix3] old block not found; aborting")

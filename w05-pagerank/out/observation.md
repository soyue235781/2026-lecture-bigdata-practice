# Week 05 observations

## Task 1
In the broken version, a dead end sends its rank nowhere, so that probability is discarded (total 0.0000 after 100 steps); the repaired version redistributes dangling mass uniformly and preserves total 1.000000.
Redistribution prevents leakage, while teleport supplies every node and lets surfers escape traps: broken C+D = 1.0000, but repaired A = 0.0375 and B = 0.0694; teleport alone would not conserve mass without the dangling repair.
Beta is the probability of following an outgoing link; with probability 1-beta the surfer jumps to a uniformly chosen node, and at a dead end the link-following branch also chooses uniformly.

## Task 2
As beta rose from 0.5 to 0.99, iterations rose 14 to 24 because less teleport weakens contraction; increasing nodes 1,200 to 20,000 at beta 0.85 changed iterations only 20 to 21 but time 0.007356 to 0.147544 s, since each pass handles more edges.
Tightening tolerance 1e-6 to 1e-10 raised iterations 12 to 20, averaging two extra iterations per requested decimal digit, and time 0.005069 to 0.007356 s.
The first sampled Top 10 order change was at beta 0.7 (p00004 and p00000 swapped); membership never changed across the five betas, so trusting a published order still requires knowing beta and checking score sensitivity.

## Task 3
I store integer adjacency indices and dangling indices in O(V+E) space, plus two O(V) rank vectors; reported float storage is conservatively 2V+16 = 2,416 including scalar temporaries, compared with the harness's V^2 = 1,440,000 matrix floats (Python overhead is excluded).
Teleport and dangling redistribution each add one common scalar to every vector entry in O(V), so neither needs a V-by-V matrix; total work per iteration is O(V+E).
The supplemental full-precision run gave maximum per-node difference 1.166e-15, caused by floating-point summation/multiplication order, with sums 0.9999999999999958 (dense) and 1.0000000000000016 (sparse); 0.529930 vs 0.007355 s means 72.05x faster and 596.03x fewer reported floats, earning strong.

# PageRank convergence experiments

## Environment and method

All eight runs were measured on the local Windows PC through Codex desktop on 2026-10-19 (KST). CPU: 12th Gen Intel Core i7-12700F; physical RAM reported by Windows: 34,212,790,272 bytes (31.86 GiB, nominal 32 GB); OS: Windows 11 build 26200; Python: 3.12.14 (bundled runtime). Available RAM was about 6.78 GiB during the runs. Major background processes observed before measurement included Discord, Microsoft Edge, LeagueClient, LeagueClientUxRender, ChatGPT, OverwolfBrowser, and Chrome, alongside Codex and measurement Python. This was not an idle-system or exhaustive process audit.

Each condition uses bench.build(seed=246), uniform initial ranks, and at most 500 iterations. Convergence means consecutive rank vectors have L1 difference strictly below tol. Each time is one perf_counter wall-clock measurement including indexing and iteration, excluding graph construction and result writing. All runs converged before the cap; no normalization was applied. The JSON stores conditions, edges, environment, timestamps, final L1 changes, rank sums, Top 10 nodes, and their scores.

Prediction recorded before execution: graph growth should increase per-iteration work and total time; iteration count need not increase because graph mixing and beta, rather than node count alone, control contraction.

## Beta and time (1,200 nodes, 5,877 edges, tol = 1e-10)

| Beta | Iterations | Seconds | Final L1 change |
|---|---:|---:|---:|
| 0.5 | 14 | 0.005598 | 2.278e-11 |
| 0.7 | 17 | 0.006235 | 5.324e-11 |
| 0.85 | 20 | 0.007356 | 7.369e-11 |
| 0.95 | 23 | 0.008718 | 4.742e-11 |
| 0.99 | 24 | 0.008795 | 5.235e-11 |

Observed: iterations increased 14, 17, 20, 23, 24 as beta rose from 0.5 to 0.99; wall time rose from 0.005598 to 0.008795 s. Mathematical explanation: for fixed graph and beta < 1, the repaired stochastic transition gives an L1 contraction bounded by beta. As beta approaches 1 this worst-case bound weakens and teleport becomes less frequent. Actual rates also depend on the graph spectrum and starting vector; these results do not prove that every graph must follow the same curve. At beta = 1 uniqueness and convergence can fail on reducible or periodic graphs.

## Graph size: iterations and total time

| Nodes | Edges | Beta | Iterations | Seconds |
|---:|---:|---|---:|---:|
| 1,200 | 5,877 | 0.85 | 20 | 0.007356 |
| 1,200 | 5,877 | 0.95 | 23 | 0.008718 |
| 20,000 | 101,665 | 0.85 | 21 | 0.147544 |
| 20,000 | 101,665 | 0.95 | 24 | 0.170389 |

Nodes grew 16.67x and edges grew 17.30x (5,877 to 101,665). At beta 0.85 the count changed 20 to 21, and at 0.95 it changed 23 to 24: only one extra iteration, rather than a proportional rise. Total times grew 20.06x at beta 0.85, 19.54x at beta 0.95. This supports the prediction: each O(V+E) pass costs more even when the number of passes is similar. Different sizes are different generated graphs, including different dead ends, so the one-iteration increase cannot be attributed to size alone.

## Tolerance (1,200 nodes, beta = 0.85)

| Tolerance | Iterations | Seconds | Final L1 change |
|---|---:|---:|---:|
| 1e-06 | 12 | 0.005069 | 4.536e-07 |
| 1e-10 | 20 | 0.007356 | 7.369e-11 |

Tightening tolerance from 1e-6 to 1e-10 adds 8 iterations over four decimal orders, averaging 2 iterations per extra requested digit. Time increased 1.45x (0.005069 to 0.007356 s). This measures a stopping threshold, not a guarantee of ten correct digits in every score. For beta < 1, a conservative fixed-point L1 error bound for the returned vector is beta * final_delta / (1-beta). Extra iterations reduce this bound but do not eliminate floating-point rounding.

## Top 10 stability

These comparisons use exactly the same 1,200-node graph, seed 246 and tol = 1e-10. Nodes are listed from highest to lowest score.

| Beta | Ordered Top 10 |
|---|---|
| 0.5 | p00009, p00001, p00006, p00005, p00003, p00002, p00000, p00004, p00007, p00008 |
| 0.7 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.85 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.95 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |
| 0.99 | p00009, p00001, p00006, p00005, p00003, p00002, p00004, p00000, p00007, p00008 |

The first observed order change is at sampled beta 0.7 relative to 0.5: p00004 overtakes p00000 (positions 7 and 8 swap). The order remains unchanged at the later sampled values. No Top 10 membership change occurs anywhere in the five samples: all contain p00000 through p00009. The exact crossover beta within (0.5, 0.7] was not measured. Stable membership does not imply stable order or scores: p00009 rises from 0.050505 to 0.174193. A published ranking should disclose beta and check sensitivity, especially for close scores.

## Limits

Timings are single measurements on a busy local PC; scheduler activity, cache state and timer noise affect millisecond-scale comparisons. They are not repeated-run averages or universal speed claims. One seed, one graph family and a sparse beta grid limit generalization. The generator creates different graphs at different sizes. Float counts in the separate benchmark are storage proxies, not total Python heap bytes; integer adjacency lists, dictionaries and object overhead also consume memory. See observation.md for sparse correctness and measured speed.

# Supplementary initialization and bounds measurements

Measured 2026-11-03 KST. Reproduce with `python measure_lab.py`. Raw data, all 80 initialization runs and full benchmark instrumentation are in measurements.json. The supplied bench.py and test_tasks.py are unchanged.

## Task 1: 40 seeds (0 through 39)

Success requires exactly the original three groups of three points, independent of label numbering; it is not merely an SSE threshold. Every run was repeated and checked for exact reproducibility.

| Initialization | Min SSE | Max SSE | Mean SSE | Successes | Success rate |
|:---|---:|---:|---:|---:|---:|
| random | 0.120000 | 96.105000 | 31.313250 | 27/40 | 67.5% |
| ++ | 0.120000 | 0.120000 | 0.120000 | 40/40 | 100.0% |

Random selects distinct input indices without replacement. K-means++ selects the first input index uniformly, then samples using D-squared weights relative to the nearest selected centre. The implementation incrementally updates nearest squared distances, using n*(k-1)=18 initialization distance calls on the 9-point, k=3 example, versus zero initialization distance calls for random selection. Those 18 calls describe the implemented loops, not a separately timed initialization benchmark. If every weight is zero, an unchosen index is selected, allowing repeated coordinates without selecting the same index twice. Both methods use a local seeded random generator and copy centroid coordinates.

The empty-cluster policy in Task 1 chooses the input point farthest from the populated/reseeded centres, breaking ties in input order. For points 0 and 10 both assigned to cluster 0, update yields centres 5 and 0; the next assignment is [1,0]. Retaining a previous empty centre at 100 would instead yield 5 and 100, with next labels [0,0]. This checked example is stored in measurements.json. The update interface has no previous-centroid argument, so retaining it would require extra state or a changed interface. Reseeding can revive an empty cluster; keeping the old centre may leave it empty but preserve its previous location. Duplicate coordinates can still make some clusters remain empty; there is no division by zero.

K-means++ traded a small seeding cost for 40/40 recoveries instead of 27/40 on this dataset. Random or supplied warm starts can be preferable when runs are extremely short, n*k*d is large, good previous centres are available, or many cheap random restarts are acceptable. This one tiny dataset does not prove that ++ always succeeds. The globally optimal SSE is nonincreasing with k, with SSE=0 possible at k=n, so selecting k only by minimum SSE overfits; use an elbow, validation, stability or domain meaning. Individual local-optimum runs need not be monotonic in k.

## Task 3: safe Hamerly-style bounds

For each point x assigned to a, store upper bound u >= d(x,c_a) and lower bound l <= min_{j != a} d(x,c_j). Also compute s_a = 0.5 * min_{j != a} d(c_a,c_j). If u is safely smaller than l or s_a, assignment cannot change: the lower-bound condition is direct, and the separation condition follows from d(x,c_j) >= d(c_a,c_j)-d(x,c_a). Otherwise tighten u by measuring d(x,c_a), test again, then do a complete ascending-index scan when necessary.

When centres move by m_j, update u <- u + m_a and l <- max(0,l-max_j m_j). The latter is conservative even though it includes the assigned centre's movement. Bounds are rounded outward, and pruning uses a relative/absolute safety slack of 1e-10*(1+|u|+|bound|), exceeding the baseline's 1e-12 tie tolerance. Ambiguous ties go through the same ascending scan and `d < best - 1e-12` rule. The unchanged _means helper retains previous centres for empty clusters exactly as NaiveKMeans does. This Task 3 policy intentionally matches its baseline, while Task 1's separate interface uses reseeding. Both algorithms stop after stable labels and use the same maximum iteration cap.

There is no approximation or uncounted distance implementation in YourKMeans: initial assignments, own-centre tightening, candidate scans, centroid separation and centroid movement all call the supplied distance callable. SSE is computed afterward by the unchanged harness, outside the scored run for both algorithms.

| Metric | Baseline | Yours |
|:---|---:|---:|
| Distance calls | 10,320,000 | 1,150,986 |
| SSE | 10737882.944550687447 | 10737882.944550687447 |
| Iterations | 43 | 43 |
| Seconds (instrumented supplemental run) | 33.2469 | 6.1414 |

Distance reduction is **88.847035% (Strong)**. SSE difference is exactly 0.0 in Python, and the full labels and centroid tuples are exactly identical, not merely within the 0.1% tolerance. An additional 132 baseline comparisons cover random integer point clouds, exact/near ties, duplicate initial centres, empty clusters, k=1 and iteration caps 1/2/50. These compare full labels, centres and iteration counts. Such tests support the invariant argument rather than replacing it.

| Distance category | Calls |
|:---|---:|
| initial | 240,000 |
| reassignment | 791,802 |
| tightening | 115,908 |
| separation | 2,772 |
| movement | 504 |

These categories sum to 1,150,986, independently checked against the supplied counter. Of those, 2,772 centre-centre separation calls (66 per later iteration) and 504 centre-motion calls are explicitly included. Bounds require O(n) scalar updates per changed iteration and O(k^2) separation work, in exchange for avoiding most O(n*k) point-centre evaluations.

The first iteration cannot prune: it uses 240,000 point-centre distances plus 12 centre movements, totaling 240,012 calls or 20.853% of all calls. Counting only the initial point-centre comparisons gives 20.852%; the convention is stated so bookkeeping is not hidden.

Observed skip counts, tested in this order: lower bound 510,581; centre separation 213,511; after tightening 43,926. Thus the maintained second-nearest lower bound accounts for the largest number of skips in this implementation. These are point-iteration decisions, not a claim of a separately measured causal speed-up for each condition; changing test order changes attribution.

Two array('d') bounds per point cost 320,000 payload bytes (16*n = 320,000 bytes, 312.5 KiB at n=20,000), plus Python array headers. Labels are also required by the baseline. Additional O(k) separation/movement/centroid state, a temporary k-distance list, dictionaries of instrumentation counts and 43 per-iteration totals also use memory; 320,000 bytes is only bound payload, not total process memory. An Elkan-style n*k lower-bound table would need 1,920,000 bytes of double payload for the lower bounds alone at these n,k. Maintaining bounds, checking them in Python and recomputing centre distances are real overhead, but the measured supplemental run still reduces time from 33.247s to 6.141s. Speed ratios depend on background load and Python overhead; only the supplied distance-call metric determines the grade.

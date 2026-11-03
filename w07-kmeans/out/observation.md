# Week 07 observations

Measured 2026-11-03 KST on the local Windows PC. Full tables and methods: curse.md and analysis.md; original measurements: curse.json and measurements.json.

## Task 1

For an empty cluster I reseed at the point farthest from existing nonempty/reseeded centres because update() has no previous-centroid argument; retaining the old centre could preserve an empty group instead (the checked 0/10 example in analysis.md gives different next labels). On seeds 0..39, random found the three blobs 27/40 times (67.5%, SSE min/max/mean 0.120/96.105/31.31325), while k-means++ succeeded 40/40 (100%, SSE always 0.120).
K-means++ spends D-squared seeding distances to avoid poor local optima: this implementation uses n*(k-1)=18 such calls for nine points and k=3, but warm starts or very short runs may make that extra cost undesirable. Optimal SSE decreases or stays equal as k grows and reaches zero at k=n, so choosing k only by minimizing SSE overfits; individual local-optimum runs can also be nonmonotonic.

## Task 2

With 1,000 points and exactly 20,000 sampled non-self pairs per dimension, contrast first drops below 1 at measured d=50 (0.982435) and below 0.5 at d=200 (0.371795); these are grid observations, not universal critical dimensions. Mean distances follow roughly sqrt(d/6), the RMS prediction rather than exactly E[D], while relative SD falls from 0.475949 at d=2 to 0.041393 at d=200; relative SD is steadier than an extreme-based contrast.
At fixed d=20, n=1,000/2,000/5,000 gives contrast 2.252741/2.448282/2.401472 with the same 20,000 sampled pairs, showing finite-data/sampling dependence without a monotonic n trend. These sampled min/max values are not exact all-pairs extremes. Jaccard LSH on sparse correlated shingle sets does not directly inherit this uniform-hypercube Euclidean result; its actual similarity distribution and near-duplicate separation must be checked.
The local i7-12700F / 31.86 GiB / Windows 11 / CPython 3.12.14 ran with OverwolfBrowser, Edge, Discord and ChatGPT active; the largest condition (2,000 points, 1,000 dimensions) took 1.9908s. All 11 conditions and their timestamps are preserved.

## Task 3

My Hamerly-style algorithm stores an upper and competitor lower bound per point (two doubles: 16*n = 320,000 payload bytes at n=20,000, plus headers and other state). Triangle inequality updates them by centre movements; safe upper/lower or half-centroid-separation tests skip scans, otherwise the own-centre distance is tightened and an ascending full scan resolves uncertainty with the baseline's tie tolerance. Empty clusters keep previous centres exactly as in NaiveKMeans.
The competitor lower bound is the largest recorded skip category: 510,581 point-iterations, versus 213,511 separation skips and 43,926 skips after tightening (order-dependent attribution). Maintenance costs O(n) bound updates, 2,772 separation distances and 504 movement distances, all counted through the supplied callable. Total distance calls fall from 10,320,000 to 1,150,986 (88.847%, Strong), with 43 iterations and exactly equal labels, centroids and SSE 10,737,882.944550687 (difference 0.0), because pruning only preserves provably unchanged assignments.
The first iteration contributes 240,012 calls, including 12 centre movements, or 20.853% of the optimized total; its 240,000 initial point-centre distances cannot be pruned. The manual R5 argument is documented here and in analysis.md despite its automatic SKIP status.

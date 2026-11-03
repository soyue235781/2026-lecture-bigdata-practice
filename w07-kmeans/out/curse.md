# Task 2: distance concentration

## Purpose and environment (A1, A7)

Measured on 2026-11-03 KST; JSON records actual UTC timestamps. CPU: 12th Gen Intel(R) Core(TM) i7-12700F, 20 logical CPUs. RAM: 34,212,790,272 bytes (31.86 GiB); available RAM at measurement start: 8.71 GiB. OS: Windows-11-10.0.26200-SP0; CPython 3.12.14. Executed on the user's local Windows PC through Codex's restricted execution process, not a remote host.
A host Get-Process snapshot during experiments showed OverwolfBrowser, Edge, Discord, ChatGPT and Memory Compression. No applications were closed. Results are single runs under ordinary background load.

## Method and sampling

Coordinates are independently uniform on [0,1]. Each condition uses base seed 246 and effective seed 246 + dimension. Exactly 20,000 pairs with different point indices are sampled with replacement; repeated index pairs are allowed. The original starter skipped self-pairs and therefore measured fewer than 20,000 distances; I changed it to resample until exactly 20,000 valid pairs have been collected. This makes the A6 comparison use equal sample counts. Timings include generating the points and sampling/calculating distances, but exclude summary statistics and writing files. Every completed row is saved immediately; prior rows are retained.

The minimum/maximum below are sampled pair-distance extremes, not exact nearest/farthest distances over all possible pairs, and not per-point nearest-neighbour distances. Standard deviation uses denominator 20,000 (the population SD of the sampled values). MB/RAM measurements are not inferred from timing.

Commands actually executed using the bundled Python executable (shown as python):

```text
python task2_curse.py --dims 2,5,10,20,50,100,200
python task2_curse.py --dims 500,1000 --points 2000
python task2_curse.py --dims 20 --points 2000
python task2_curse.py --dims 20 --points 5000
```

## Measurements (A2, A4, A5)

| d | Points | Pairs | Min | Max | Mean | SD | Contrast | Relative SD | sqrt(d/6) | Mean/theory | Seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1000 | 20000 | 0.002707 | 1.325542 | 0.521040 | 0.247988 | 488.581595 | 0.475949 | 0.577350 | 0.902467 | 0.0217 |
| 5 | 1000 | 20000 | 0.110600 | 1.687379 | 0.884282 | 0.248962 | 14.256630 | 0.281541 | 0.912871 | 0.968683 | 0.0283 |
| 10 | 1000 | 20000 | 0.438454 | 2.159465 | 1.273457 | 0.245506 | 3.925179 | 0.192787 | 1.290994 | 0.986415 | 0.0368 |
| 20 | 1000 | 20000 | 0.820812 | 2.669888 | 1.815214 | 0.245437 | 2.252741 | 0.135211 | 1.825742 | 0.994234 | 0.0529 |
| 50 | 1000 | 20000 | 1.909192 | 3.784850 | 2.867193 | 0.237941 | 0.982435 | 0.082988 | 2.886751 | 0.993225 | 0.1109 |
| 100 | 1000 | 20000 | 3.205749 | 4.953536 | 4.068080 | 0.243200 | 0.545204 | 0.059782 | 4.082483 | 0.996472 | 0.2126 |
| 200 | 1000 | 20000 | 4.870873 | 6.681838 | 5.776168 | 0.239091 | 0.371795 | 0.041393 | 5.773503 | 1.000462 | 0.3885 |
| 500 | 2000 | 20000 | 8.099089 | 10.175804 | 9.126251 | 0.240508 | 0.256413 | 0.026353 | 9.128709 | 0.999731 | 0.9891 |
| 1000 | 2000 | 20000 | 11.970473 | 13.806368 | 12.908707 | 0.239883 | 0.153369 | 0.018583 | 12.909944 | 0.999904 | 1.9908 |
| 20 | 2000 | 20000 | 0.820812 | 2.830391 | 1.817621 | 0.243126 | 2.448282 | 0.133760 | 1.825742 | 0.995552 | 0.0586 |
| 20 | 5000 | 20000 | 0.795901 | 2.707236 | 1.809824 | 0.244218 | 2.401472 | 0.134940 | 1.825742 | 0.991282 | 0.0636 |

## Contrast thresholds (A3)

For the controlled 1,000-point sweep, contrast first falls below 1 at the measured dimension 50 (0.982435), after 2.252741 at dimension 20. It first falls below 0.5 at dimension 200 (0.371795), after 0.545204 at 100. Thus the observed crossing brackets are (20, 50] and (100, 200] on this grid; the exact first integer dimension is unmeasured. These are data/seed/sample-dependent crossings, not universal critical dimensions. The additional 2,000-point runs at 500 and 1,000 dimensions have contrasts 0.256413 and 0.153369; their point count differs, so they are separately labelled and do not refine the controlled crossing brackets.

## Why means rise but distances become less informative (A4, A5)

For independent uniform coordinates, E[(X-Y)^2] = 1/6, so E[D^2] = d/6. Thus sqrt(d/6) predicts an RMS distance, and approximates the mean better at high dimension; sqrt(E[D^2]) is not exactly E[D]. The means are 0.521040 at d=2, 5.776168 at d=200 and 12.908707 at d=1,000, consistent with square-root growth rather than linear growth. The dimension-1,000 mean is about 24.77 times the dimension-2 mean, not 500 times. The mean/theory ratio rises from 0.902467 at d=2 to nearly 1 at high dimensions. Sampling error can put an empirical mean slightly above the population RMS prediction, as at d=200; this does not contradict Jensen's inequality for population expectations.

Each new coordinate adds a nonnegative squared-distance term, so average squared distances grow in proportion to d. However, independent contributions average out in relative terms. Relative SD falls from 0.475949 at d=2 to 0.041393 at d=200 and 0.018583 at d=1,000, while absolute SD remains around 0.24. Near/far distances become similar relative to their growing mean. Relative SD describes the whole sampled distribution and is more stable here than contrast, which divides by a potentially tiny sampled minimum (0.002707 at d=2) and depends strongly on extreme observations and sample coverage. Neither metric proves that every possible nearest-neighbour task has failed.

## Fixed-dimension point-count comparison (A6)

At d=20 with exactly 20,000 sampled pairs and the same effective seed 266, n=1,000/2,000/5,000 gives contrast 2.252741/2.448282/2.401472. The corresponding sampled minima are 0.820812/0.820812/0.795901, and maxima are 2.669888/2.830391/2.707236. Relative SD stays close to 0.135211/0.133760/0.134940.

Changing n affects the finite point cloud, which index pairs are sampled, the available pair pool and its coverage. More points can introduce closer or farther pairs if all pairs are examined, but here the number of sampled distances stays fixed, so a monotonic contrast increase is not guaranteed and was not observed. The same seed makes runs reproducible and the coordinate clouds share prefixes at fixed d, but generating more coordinates consumes more random numbers before sampling. Thus pair identities differ between conditions, and one run per n cannot isolate a universal population effect of n. A stronger study would repeat multiple seeds and separately vary sampled pair count.

## Connection to Week 03 Jaccard LSH (A8)

Week 03 uses shingle sets, Jaccard similarity |A intersection B| / |A union B|, MinHash and banding. This experiment uses real-valued vectors, Euclidean distance and independent uniform coordinates. The large number of possible shingles is not a reason to transfer the uniform-hypercube Euclidean results directly to Jaccard LSH: text shingles are sparse, correlated and may have genuine duplicate/near-duplicate structure. MinHash collision probability targets Jaccard similarity, not Euclidean distance.

The shared risk is an uninformative empirical similarity distribution: if meaningful neighbours cannot be distinguished from unrelated data, candidate selection or clustering becomes less useful. If most Jaccard similarities are nearly equal, LSH may offer poor discrimination or an unfavorable candidate/recall trade-off. Actual shingle-set similarity distributions, thresholds and banding must be inspected; high dimensionality alone does not make LSH unusable.

## Limits and largest run

The largest condition (2,000 points, d=1,000, 20,000 sampled pairs) completed in 1.9908 seconds; this was also the longest Task 2 run. The full table records every condition. These are synthetic uniform data, one seed per condition, sampled extremes and single-run timings; they do not measure exact all-pairs extremes or performance on real sparse/structured data. No experiment failed, and no unmeasured threshold is claimed.

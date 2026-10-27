# Task 2: measured threshold curve

Measured on 2026-10-28 KST (raw timestamps use UTC). This is the user's local Windows desktop running a Codex restricted execution process, not a remote Linux host.

## Environment and measurement

CPU: 12th Gen Intel(R) Core(TM) i7-12700F (20 logical CPUs); RAM: 34,212,790,272 bytes (31.86 GiB), with 17.28 GiB available at the start of the additional sweep. OS: Windows-11-10.0.26200-SP0; Python: 3.12.14 (bundled CPython).
A host process snapshot during the experiments showed Discord, ChatGPT, Microsoft Edge, Adobe Creative Cloud UI Helper and Memory Compression. These programs were left running; this is not an idle-machine benchmark. The restricted process alone could not enumerate all host programs, so the extra snapshot is recorded separately in explosion.json.

All runs use the unchanged bench.build(): seed 246, 20,000 baskets, 2,000 item universe, support as an absolute basket count. The same generated baskets are reused within each invocation. Time includes tracemalloc overhead; peak memory is traced Python allocation during the algorithm, including counters and returned results, excluding prebuilt baskets and tracing internals. It is not total PC RAM or process RSS. Decimal MB = 1,000,000 bytes. Each completed row is immediately appended and atomically saved; MemoryError or interruption is saved separately if encountered. No runs failed or were stopped.

Commands actually executed (using the bundled Python executable because the Windows python alias was unavailable):

```text
python task2_explosion.py --supports 400,200,100,50,25
python task2_explosion.py --supports 12,6,3,1
```

## Results

| Support | Frequent pairs | Peak counters | Seconds (traced) | Peak Python MB | Status |
|---:|---:|---:|---:|---:|:---|
| 400 | 249 | 10,585 | 0.591 | 1.057 | success |
| 200 | 776 | 58,626 | 1.159 | 6.383 | success |
| 100 | 2,244 | 273,701 | 2.192 | 26.392 | success |
| 50 | 6,397 | 820,259 | 3.683 | 102.174 | success |
| 25 | 17,045 | 893,456 | 3.774 | 102.171 | success |
| 12 | 43,116 | 893,456 | 4.205 | 102.830 | success |
| 6 | 101,938 | 893,456 | 4.253 | 119.356 | success |
| 3 | 250,054 | 893,456 | 4.727 | 156.592 | success |
| 1 | 893,456 | 893,456 | 5.952 | 327.024 | success |

## Growth rates (A4 and A5)

| Support change | Threshold decrease | Counter multiplier | Answer multiplier |
|:---|---:|---:|---:|
| 400 -> 200 | 2.00x | 5.539x | 3.116x |
| 200 -> 100 | 2.00x | 4.669x | 2.892x |
| 100 -> 50 | 2.00x | 2.997x | 2.851x |
| 50 -> 25 | 2.00x | 1.089x | 2.665x |
| 25 -> 12 | 2.08x | 1.000x | 2.530x |
| 12 -> 6 | 2.00x | 1.000x | 2.364x |
| 6 -> 3 | 2.00x | 1.000x | 2.453x |
| 3 -> 1 | 3.00x | 1.000x | 3.573x |

For the first three halvings, counters grow 5.539x, 4.669x and 2.997x, each more than doubling. Candidate growth then slows to 1.089x at 50 -> 25 and stops entirely below 25. In contrast, answers grow about 3.116x, 2.892x, 2.851x and 2.665x through the required sweep. The exact measured ratios in the table are the source of truth, not a claim that every halving behaves the same way.

Many individual items become frequent before their pairs do. If F items survive, up to F(F-1)/2 pairs can require counters, including pairs that never reach the threshold. At support 50 there are 820,259 counters for only 6,397 answers (128.23 counters per answer). Thus a slightly lower threshold can create much more intermediate work than useful output. Once all 2,000 items survive (support 25 here), all 893,456 distinct observed pairs already have counters; lowering support changes which are returned, rather than creating more counters. At support 1 every observed pair is an answer, which makes output allocation substantial.

## Actual limit and interpretation (A2)

No failure or genuinely unbearable threshold was reached. We continued beyond the requested support 3 to support 1, the smallest positive integer threshold. The largest run completed in 5.952 traced seconds with 327.024 MB peak Python allocations. It would be false to claim that RAM or a time limit was exhausted. At support 1 the unavoidable output grows to 893,456 frozenset keys while the counter table is still live; this explains the rising peak memory even after counters plateau. Pair enumeration and hash-table updates dominate the work, with result allocation adding cost at the lowest thresholds; this is an algorithmic interpretation, not a sampled CPU profile.

This fixed 20,000-basket dataset saturates before the 31.86 GiB machine runs out of resources. Increasing items or baskets could reach a hardware limit, but that would change the assigned dataset and extend a late submission. No artificial out-of-memory run was attempted. A2's literal request for an unbearable point therefore remains unobserved; the measured range and reason are explicit. These are single runs, not averaged performance estimates, and tracing changes timings. Full Python/process memory comparisons for PCY are in pcy_analysis.md and measurements.json.

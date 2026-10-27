# PCY bucket and memory experiments

Measured on 2026-10-28 KST on the environment described in explosion.md. Reproduce with `python measure_experiments.py`; existing cases are preserved and skipped. All cases use support 50 and prefixes of the same fixed-seed dataset. Each algorithm runs in a fresh Python process. Timings below include tracemalloc and should not be compared with the ordinary bench.txt timings.

## Correctness and measurement boundaries

All 15 measured algorithm configurations have matching SHA-256 digests of sorted (pair, exact support count) results within each dataset size. This checks more than the supplied harness, which compares only pair keys. An additional 36 randomized PCY cases (each run twice to check instance reuse) matched brute-force counts with empty baskets, duplicate items, supports 1/2/5, and 1/7/1,024 buckets; Task 1 was checked against the same brute-force answers.

Peak counters means all simultaneously live entries in the pass-two pair Counter, before final filtering. It excludes bucket counts, singleton counts and the returned result dictionary, following the supplied baseline's metric. Total memory measurements include the result dictionary while the Counter is still live. No pair counters are discarded early or omitted from the peak. Pass one counts every deduplicated basket's pairs into unsigned 64-bit bucket entries, then converts frequent buckets to a genuinely bit-packed bitmap; it frees the array before pass two. Python object headers, singleton tables, deterministic ID maps, per-basket temporary lists, and final output are all included by tracemalloc.

Peak Python MB means maximum traced algorithm allocations, excluding the prebuilt baskets, interpreter, allocator retention and tracing overhead. Peak process MB is Windows GetProcessMemoryInfo.PeakWorkingSetSize from a fresh child process, including all those costs and the input. Working set is resident process memory, not virtual memory or whole-machine RAM. The build always creates 20,000 baskets before slicing; this input-generation high-water mark can mask small algorithm differences in process peaks. Each value is a single run with background programs still running.

## Bucket-size comparison: 20,000 baskets

| Buckets | Peak counters | Cut | Frequent buckets | Frequent ratio | Distinct-pair collisions | Array bytes | Bitmap bytes | Peak Python MB | Peak process MB | Traced seconds |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4,096 | 820,259 | 0.000% | 4,096 | 100.000% | 889,360 | 32,768 | 512 | 102.411 | 234.430 | 24.053 |
| 65,536 | 315,924 | 61.485% | 21,715 | 33.134% | 827,988 | 524,288 | 8,192 | 30.291 | 120.766 | 19.218 |
| 1,048,576 | 13,440 | 98.361% | 6,971 | 0.665% | 300,227 | 8,388,608 | 131,072 | 8.859 | 62.566 | 17.472 |
| 4,194,304 | 7,854 | 99.042% | 6,500 | 0.155% | 90,141 | 33,554,432 | 524,288 | 34.418 | 87.835 | 21.580 |

Baseline: 820,259 counters, 6,397 answers, 102.287 MB peak Python allocation, 234.193 MB peak process working set, 3.647 traced seconds.

The support-1 sweep found exactly 893,456 distinct observed pairs. Here "distinct-pair collisions" is that number minus nonempty buckets after hashing ALL observed pairs. It counts excess distinct pair mappings beyond the first pair in each occupied bucket; it is not the number of colliding occurrences, and not every collision causes a false candidate. Every result still contains exactly 6,397 frequent pairs with identical support counts.

Selected **1,048,576 buckets**: 8,388,608 bytes (8 MiB) of array payload, then 131,072 bytes (128 KiB) of bitmap payload. During conversion they briefly coexist; measured peak includes that overlap and object headers. It reduces pair counters by 98.361% to 13,440. The 4,194,304-bucket version only removes 5,586 more counters but needs a 32 MiB array and reaches 34.418 MB traced peak, so it is a worse memory trade-off. With just 4,096 buckets all buckets are frequent, collisions make the filter useless, and all 820,259 counters remain. The 65,536-bucket setting improves pruning but retains 315,924 counters and uses 30.291 MB traced peak, also more than the selected setting.

On the full dataset the selected PCY's traced peak is 8.859 MB versus 102.287 MB (91.34% lower). Fresh-process peak working set is 62.566 MB versus 234.193 MB (73.28% lower). Thus this is an actual total-memory improvement in this measured instrumented process, not merely a smaller pair-counter number. PCY pays for hashing every pair in pass one and checking the bitmap in pass two, so its traced runtime is longer. The normal benchmark timing is recorded separately in bench.txt.

## Crossover: fixed 1,048,576 buckets, absolute support 50

| Baskets | Baseline counters | PCY counters | Baseline Python MB | PCY Python MB | Baseline process MB | PCY process MB |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0 | 0 | 0.058 | 8.614 | 54.157 | 53.314 |
| 500 | 136 | 13 | 0.113 | 8.713 | 53.510 | 53.694 |
| 2,000 | 6,228 | 183 | 0.831 | 8.728 | 53.105 | 53.432 |
| 5,000 | 50,168 | 902 | 6.488 | 8.754 | 53.223 | 53.600 |
| 10,000 | 212,340 | 3,009 | 25.630 | 8.756 | 83.825 | 53.445 |
| 20,000 | 820,259 | 13,440 | 102.287 | 8.859 | 234.193 | 62.566 |

For this prefix experiment, the measured algorithm-allocation crossover lies between 5,000 baskets (6.488 MB baseline vs 8.754 MB PCY) and 10,000 baskets (25.630 MB vs 8.756 MB). Fresh-process peaks also show a clear advantage at 10,000 (83.825 MB vs 53.445 MB) and at 20,000. The exact boundary was not measured. At 100 baskets, incidental input-building/allocator behavior even makes the process peak slightly smaller for PCY despite its much larger traced algorithm allocation; that is not evidence of an early crossover.

As a rough theoretical check, 102,287,343 / 820,259 is about 124.70 traced bytes per baseline candidate on the full dataset (including shared structures and output, not a universal entry size). Dividing the selected 8.859 MB peak by this empirical average suggests about 71,000 baseline counters are needed before PCY can win on algorithm memory. The measured prefix runs bracket this: 50,168 baseline counters at 5,000 baskets and 212,340 at 10,000. Dictionary resize steps and changing outputs prevent exact linear prediction. Crossover depends on distinct candidate pairs, popularity distribution, support, bucket count, Python implementation and returned-output size, not basket count alone. These results apply to a fixed absolute support; scaling support with dataset size would produce a different curve.

# Task 2 — local measurement curve

- CPU: 12th Gen Intel(R) Core(TM) i7-12700F
- RAM: 31.86 GiB
- OS / Python: Windows-11-10.0.26200-SP0 / 3.12.14
- Other activity: Codex desktop and Python active; other applications not audited
- Time excludes input generation. Memory is a separate tracemalloc run; peak means Python allocations during find(), excluding the existing docs and interpreter, not total process RAM.

| n | brute s | LSH s | brute comparisons | LSH comparisons | brute peak MiB | LSH peak MiB |
|---:|---:|---:|---:|---:|---:|---:|
| 250 | 0.112190 | 0.199168 | 31125 | 15 | 0.008 | 1.722 |
| 500 | 0.441928 | 0.341988 | 124750 | 29 | 0.010 | 2.827 |
| 1000 | 1.840176 | 0.660955 | 499500 | 59 | 0.012 | 4.770 |
| 2000 | 7.698900 | 1.193114 | 1999000 | 117 | 0.021 | 8.414 |
| 4000 | 30.914049 | 2.422099 | 7998000 | 246 | 0.041 | 15.616 |
| 8000 | 131.392397 | 5.046327 | 31996000 | 487 | 0.069 | 29.697 |

## Quadratic check

| n → 2n | measured brute time ratio | expected comparison ratio | fitted exponent log2(time ratio) |
|---|---:|---:|---:|
| 250 → 500 | 3.939 | 4.008 | 1.978 |
| 500 → 1000 | 4.164 | 4.004 | 2.058 |
| 1000 → 2000 | 4.184 | 4.002 | 2.065 |
| 2000 → 4000 | 4.015 | 4.001 | 2.006 |
| 4000 → 8000 | 4.250 | 4.001 | 2.088 |

Mean doubling time ratio: 4.111 (ideal quadratic: 4). Read the individual ratios above for deviations.

## Crossover and practical limit

Observed brute→LSH crossover bracket(s): 250 < n <= 500. The exact crossing needs intermediate sizes.
At small n, LSH pays to index shingles, compute 128 hash minima, and build 32 band bucket tables before verifying candidates; brute force starts comparing immediately.
- n=4000: full measurement including tracing took 87.42s; this is instrumentation waiting, not a 60s find()
- n=8000: single untraced find() reached 131.39s
- Largest n=8000: brute peak 0.069 MiB; LSH peak 29.697 MiB (traced allocations).
- Coverage: 6 distinct sizes, 32× span; A1 met.

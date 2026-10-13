# Task 2: Exact distinct counting and Flajolet-Martin

## Environment and method

- CPU: 12th Gen Intel(R) Core(TM) i7-12700F
- RAM: 31.86 GiB
- OS / Python / NumPy: Windows-11-10.0.26200-SP0 / 3.12.14 / 2.3.5
- Host: DESKTOP-VRI32HH; local Windows PC, executed through Codex desktop
- Other activity: Codex desktop and measurement Python active; other apps not audited
- Fixed seed 246; n generated strings sampled from a key space of size 0.4n. True distinct count is measured, not assumed to equal 0.4n.
- FM uses 64 trailing-zero maxima and median of group means in log space. Fixed batches of at most 256 integer hashes accelerate arithmetic; the stream is not stored.
- Each method has an untraced timing pass and a separate traced memory pass. Both include lazy input generation. Imports are completed before measurement. Peak includes allocations made during the call, including stream and FM scratch buffers; it excludes the existing interpreter/modules and is not total process RSS.

## Results

| n | true distinct | exact s | exact peak MiB | FM s | FM peak MiB | FM estimate | estimate / truth |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 100,000 | 36,702 | 0.045 | 3.744 | 0.165 | 0.393 | 60,096.8 | 1.6374 |
| 400,000 | 146,970 | 0.200 | 11.054 | 0.736 | 0.393 | 211,090.2 | 1.4363 |
| 1,600,000 | 587,625 | 0.979 | 44.487 | 3.079 | 0.393 | 597,053.2 | 1.0160 |
| 6,400,000 | 2,349,909 | 4.261 | 179.565 | 12.433 | 0.393 | 2,719,669.7 | 1.1574 |

## Growth and accuracy

| n change | n multiplier | distinct multiplier | exact memory multiplier | FM memory multiplier |
|---|---:|---:|---:|---:|
| 100,000 -> 400,000 | 4.000 | 4.004 | 2.953 | 1.000 |
| 400,000 -> 1,600,000 | 4.000 | 3.998 | 4.024 | 1.000 |
| 1,600,000 -> 6,400,000 | 4.000 | 3.999 | 4.036 | 1.000 |

Coverage: 4 distinct sizes and a 64x range; A1 met.
Across this range, exact peak grows 47.964x and FM peak grows 1.000x.
Exact retains distinct strings and a resizable set table; set resize thresholds make memory growth uneven. FM retains a fixed number of registers and bounded scratch buffers.
FM accuracy ratios range from 1.0160 to 1.6374. Fixed hash count does not promise that relative error improves with longer streams; compare each observed ratio above.
FM saves space but hashes each item 64 ways, so memory savings do not imply faster execution.

## Practical limit and limitations

The exact method did not reach a recorded time or memory limit in this measured range. This is not evidence that exact counting scales without limit.
Largest measured n=6,400,000: exact 4.261s and 179.565 MiB; FM 12.433s and 0.393 MiB.
Further sizes such as 25,000,000 are needed to locate an exact-counting hardware limit. The script estimates memory risk before running larger sizes rather than exhausting RAM.
These are single measurements on one synthetic workload with 40% key-space size. Different distinct fractions, longer strings, other running apps, or repeated timing trials could change the practical limit. FM estimates are probabilistic, not exact counts.

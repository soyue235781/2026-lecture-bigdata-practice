# Week 04 observations

## Task 1
Bloom insertion only sets bits, and lookup checks the same seeded positions, so inserted items cannot become false negatives. The predicted FP rate was 0.860%, compared with 0.905% measured over 20,000 absent items; random hash occupancy and a finite query sample explain the small difference.
For FM, I averaged R within eight groups of eight hashes, took the median, and returned 2 to that power. On 19,953 distinct items, the raw mean of 2^R gave 90,592, the median gave 16,384, and my grouped estimate gave 23,170 (1.16x); log-space grouping limits extreme values and avoids whole-power-of-two steps.
Reservoir sampling draws a position from 0 to count-1 and replaces a slot only when that position is below k. Entry probability k/count and the later survival probabilities give every stream position final probability k/n, while storing at most k items; the 4,000-trial check had an 8.9% spread.

## Task 2
On my local i7-12700F Windows PC with 31.86 GiB RAM and Python 3.12.14, exact counting did not become unbearable within the measured range: at 6,400,000 items it took 4.261 s and peaked at 179.565 MiB. Neither time nor memory was exhausted, so a larger safe experiment is needed to locate that limit.
Across four sizes spanning 64x, exact peak memory grew 47.964x, while FM grew only 1.000005x and stayed near 0.393 MiB, including its fixed scratch buffers. FM ratios were 1.6374, 1.4363, 1.0160, and 1.1574, so relative accuracy did not improve monotonically; its largest run took 12.433 s despite using far less memory.
A factor-of-two visitor estimate can be useful for a rough traffic trend, but not for billing or an exact audit. Peaks are additional traced allocations, not total process RAM; each method includes lazy input generation, and the known other activity was Codex and Python, with other apps not audited.

## Task 3
I replaced one hash with k=7: (80,000/8,000) ln(2)=6.93, with an ideal floor of about 0.82%. Python headers and the seed use 141 bytes, leaving 78,872 payload bits; k still rounds to 7, the adjusted prediction is 0.8774%, and all retained instance memory totals 80,000 bits.
The baseline had 19,023 FP (9.5115%); mine had 1,696 FP (0.8480%), zero FN, and a 91.08% FP reduction, reaching Strong. Finite-query variation and actual hash occupancy explain the gap from theory; the unmodified baseline reports 80,000 logical bits but its one-byte-per-bit array alone actually occupies 80,057 bytes.
For unknown n, I would plan capacity conservatively or add scalable Bloom layers if more memory is allowed, keeping old layers to preserve no-FN behavior. Underestimating n saturates the bits and raises FP; overestimating n wastes allocated space when sizing the filter, and either wrong estimate can choose a poor k under a fixed budget.

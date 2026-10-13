#!/usr/bin/env python3
"""Week 4 · Task 1 — Answer questions about a stream you cannot store.

Textbook §4.3 (sampling), §4.4 (Bloom filter), §4.5 (Flajolet-Martin).

The premise of the whole chapter: the stream is longer than your memory, it
goes past once, and you still have to answer. Every method here trades an exact
answer for a bounded amount of space, and the job is to know exactly what you
traded.

You build three, and the harness checks each against the truth it is
approximating.

    python3 task1_sketches.py --verify
"""
import argparse, hashlib, math, random, statistics


def _bloom_indices(item, m, k, key):
    """Double hashing gives repeatable positions without storing the items."""
    digest = hashlib.blake2b(str(item).encode("utf-8"), digest_size=16, key=key).digest()
    first = int.from_bytes(digest[:8], "little")
    step = int.from_bytes(digest[8:], "little") | 1
    for i in range(k):
        yield (first + i * step) % m


class BloomFilter:
    """Membership, with one-sided error.

    A Bloom filter never says "no" about something you inserted. It sometimes
    says "yes" about something you did not. That asymmetry is the entire design
    and it is why it is useful for "have I seen this before" and useless for
    "is this definitely in the set".

    `m` bits, `k` hash functions.
    """

    def __init__(self, m, k, seed=246):
        if m <= 0 or k <= 0:
            raise ValueError("m and k must be positive")
        self.m, self.k = m, k
        self.key = hashlib.blake2b(str(seed).encode(), digest_size=16).digest()
        self.bits = bytearray((m + 7) // 8)

    def add(self, item):
        for position in _bloom_indices(item, self.m, self.k, self.key):
            self.bits[position // 8] |= 1 << (position % 8)

    def __contains__(self, item):
        return all(self.bits[position // 8] & (1 << (position % 8))
                   for position in _bloom_indices(item, self.m, self.k, self.key))

    def expected_fp_rate(self, n_inserted):
        """The textbook's predicted false-positive rate after n insertions.

        §4.4.2 derives it. Return the number, do not measure it - the harness
        measures separately and compares the two.
        """
        if n_inserted < 0:
            raise ValueError("n_inserted must be nonnegative")
        return (-math.expm1(-self.k * n_inserted / self.m)) ** self.k


def _fm_registers(stream, n_hashes, seed):
    """Keep trailing-zero maxima; fixed batches only accelerate hash arithmetic."""
    import numpy as np

    if n_hashes <= 0:
        raise ValueError("n_hashes must be positive")
    rng = random.Random(seed)
    salts = np.array([rng.getrandbits(64) for _ in range(n_hashes)], dtype=np.uint64)
    maxima = [0] * n_hashes
    batch = []
    nonempty = False

    def update():
        # SplitMix64 mixes each salted stable hash into a uniform 64-bit value.
        values = np.asarray(batch, dtype=np.uint64)[:, None] + salts[None, :]
        values += np.uint64(0x9E3779B97F4A7C15)
        values = (values ^ (values >> 30)) * np.uint64(0xBF58476D1CE4E5B9)
        values = (values ^ (values >> 27)) * np.uint64(0x94D049BB133111EB)
        values ^= values >> 31
        lowest_bits = values & (~values + np.uint64(1))
        powers = lowest_bits.max(axis=0)
        zero_hashes = (values == 0).any(axis=0)
        for i, power in enumerate(powers):
            trailing = 64 if zero_hashes[i] else int(power).bit_length() - 1
            maxima[i] = max(maxima[i], trailing)
        batch.clear()

    for item in stream:
        nonempty = True
        digest = hashlib.blake2b(str(item).encode("utf-8"), digest_size=8).digest()
        batch.append(int.from_bytes(digest, "little"))
        if len(batch) == 256:
            update()
    if batch:
        update()
    return maxima if nonempty else []


def flajolet_martin(stream, n_hashes=64, seed=246):
    """Estimate how many DISTINCT items went past, in almost no memory.

    §4.5. Hash each item, count trailing zeros in the hash, keep the maximum.
    A maximum of R suggests about 2^R distinct items, because seeing R trailing
    zeros is a 1-in-2^R event.

    One hash gives an estimate with enormous variance, so you use many and
    combine them. How you combine them matters a great deal:

      * averaging 2^R directly is dominated by whichever hash got lucky - the
        values are exponential, so one outlier swamps the rest
      * the median is robust but can only ever be a power of two
      * §4.5.3 suggests grouping, and combining twice

    The harness accepts anything **within a factor of two** of the truth. That is
    not a generous tolerance, it is an honest one: this method really is that
    crude, and HyperLogLog exists because of it. Getting inside a factor of two
    reliably is the requirement; getting closer than that is not expected here.

    Return your estimate as a float.
    """
    maxima = _fm_registers(stream, n_hashes, seed)
    if not maxima:
        return 0.0
    # Average in log space within groups, then take a robust median of groups.
    groups = max(1, math.isqrt(n_hashes))
    group_means = [statistics.mean(maxima[i::groups]) for i in range(groups)]
    return 2.0 ** statistics.median(group_means)


def reservoir_sample(stream, k, seed=246):
    """Keep k items uniformly at random from a stream of unknown length.

    §4.3. Every item that went past must end up with the same probability k/n
    of being in your sample, and you only ever hold k of them.

    Return a list of k items (or fewer if the stream was shorter).
    """
    if k < 0:
        raise ValueError("k must be nonnegative")
    rng = random.Random(seed)
    sample = []
    for count, item in enumerate(stream, start=1):
        if count <= k:
            sample.append(item)
        else:
            # Each new item enters with probability k/count.
            position = rng.randrange(count)
            if position < k:
                sample[position] = item
    return sample


# ------------------------------------------------------------------- harness
def verify():
    fails = 0
    rng = random.Random(246)

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<46} {detail}")
        fails += not ok

    # --- Bloom: no false negatives, ever
    try:
        bf = BloomFilter(m=8192, k=5)
    except NotImplementedError:
        print("  BloomFilter is still a stub"); return 1
    inserted = [f"item-{i}" for i in range(800)]
    for x in inserted:
        bf.add(x)
    check("no false negatives", all(x in bf for x in inserted))

    absent = [f"other-{i}" for i in range(20_000)]
    fp = sum(1 for x in absent if x in bf) / len(absent)
    predicted = bf.expected_fp_rate(len(inserted))
    close = abs(fp - predicted) < max(0.02, predicted * 0.5)
    check("measured false-positive rate matches theory", close,
          f"measured {fp:.3%}, predicted {predicted:.3%}")

    # --- Flajolet-Martin: a factor of two is what this method gives you
    try:
        distinct = 20_000
        stream = [f"k{rng.randrange(distinct)}" for _ in range(120_000)]
        est = flajolet_martin(stream)
    except NotImplementedError:
        print("  flajolet_martin is still a stub"); return 1
    true_distinct = len(set(stream))
    ratio = est / true_distinct
    check("distinct estimate within a factor of 2", 0.5 <= ratio <= 2.0,
          f"estimated {est:,.0f}, true {true_distinct:,} ({ratio:.2f}x)")

    # --- Reservoir: uniform over many trials
    try:
        counts = [0] * 20
        trials = 4000
        for t in range(trials):
            s = reservoir_sample(range(20), 5, seed=t)
            for i in s:
                counts[i] += 1
    except NotImplementedError:
        print("  reservoir_sample is still a stub"); return 1
    expected = trials * 5 / 20
    spread = (max(counts) - min(counts)) / expected
    check("reservoir is uniform across items", spread < 0.15,
          f"spread {spread:.1%} around {expected:.0f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())

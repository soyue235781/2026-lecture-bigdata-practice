"""Reproduce extra correctness, bucket-size and memory crossover measurements.

Each memory measurement runs in a fresh process. Run after task2_explosion.py.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time
import tracemalloc
from itertools import combinations

import bench
from task1_apriori import association_rules, frequent_pairs, frequent_singletons
from task3_pcy import PlainApriori, YourAlgorithm

OUT = Path(__file__).resolve().parent / 'out'


def process_peak():
    if os.name != 'nt':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', ctypes.c_ulong), ('faults', ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in ('peak_working_set', 'working_set',
            'peak_paged_pool', 'paged_pool', 'peak_nonpaged_pool', 'nonpaged_pool',
            'pagefile', 'peak_pagefile')]
    info = Counters()
    info.cb = ctypes.sizeof(info)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,
                                                       ctypes.c_void_p, ctypes.c_ulong]
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(info), info.cb)
    return info.peak_working_set if ok else None


def worker(kind, size, buckets):
    baskets = bench.build()[:size]
    algo = PlainApriori(50) if kind == 'baseline' else YourAlgorithm(50, buckets)
    tracemalloc.start()
    start = time.perf_counter()
    pairs = algo.run(baskets)
    seconds = time.perf_counter() - start
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    rss = process_peak()
    # Digest includes exact support counts, not just the set of answers.
    canonical = sorted((tuple(sorted(pair)), count) for pair, count in pairs.items())
    result = dict(kind=kind, baskets=size, bucket_count=buckets if kind == 'pcy' else 0,
                  seconds=seconds, peak_bytes=peak, process_peak_working_set=rss,
                  peak_counters=algo.peak_counters, frequent_pairs=len(pairs),
                  count_digest=hashlib.sha256(repr(canonical).encode()).hexdigest())
    if kind == 'pcy':
        for attr in ('bucket_array_bytes', 'bitmap_bytes', 'frequent_buckets', 'nonempty_buckets'):
            result[attr] = getattr(algo, attr)
    print(json.dumps(result))


def correctness():
    rng = random.Random(246)
    checked = 0
    for size in (0, 1, 10, 50):
        baskets = [[rng.randrange(12) for _ in range(rng.randrange(12))]
                   for _ in range(size)]
        for support in (1, 2, 5):
            brute = {}
            for basket in baskets:
                for pair in combinations(sorted(set(basket)), 2):
                    key = frozenset(pair)
                    brute[key] = brute.get(key, 0) + 1
            expected = {pair: count for pair, count in brute.items() if count >= support}
            assert frequent_pairs(baskets, support) == expected
            for buckets in (1, 7, 1024):
                algo = YourAlgorithm(support, buckets)
                assert algo.run(baskets) == expected
                assert algo.run(baskets) == expected  # reused instance resets statistics
                checked += 1
    baskets = bench.build()
    singles = frequent_singletons(baskets, 50)
    rules = association_rules(baskets, 50, 0)
    top = rules[0]
    reverse = next(rule for rule in rules if rule[0] == top[1] and rule[1] == top[0])
    return dict(randomized_pcy_checks=checked, exact_counts=True,
                frequent_singletons=len(singles),
                theoretical_candidates=len(singles) * (len(singles) - 1) // 2,
                highest_rule=top, reverse_rule=reverse)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=('baseline', 'pcy'))
    parser.add_argument('--size', type=int, default=20000)
    parser.add_argument('--buckets', type=int, default=1 << 20)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.size, args.buckets)
        return
    OUT.mkdir(exist_ok=True)
    data = {'correctness': correctness(), 'measurements': [],
            'method': 'Fresh process per run; tracemalloc includes algorithm structures and output, excludes prebuilt baskets. Process peak working set includes interpreter, baskets and tracing overhead. Build creates all 20,000 baskets before slicing, consistently in every worker.'}
    if (OUT / 'measurements.json').exists():
        data = json.loads((OUT / 'measurements.json').read_text(encoding='utf-8'))
    cases = [('baseline', 20000, 0)] + [('pcy', 20000, count) for count in
             (4096, 65536, 1 << 20, 1 << 22)]
    cases += [(kind, size, 1 << 20) for size in (100, 500, 2000, 5000, 10000)
              for kind in ('baseline', 'pcy')]
    for kind, size, buckets in cases:
        if any(row['kind'] == kind and row['baskets'] == size and
               row['bucket_count'] == (buckets if kind == 'pcy' else 0)
               for row in data['measurements']):
            continue
        output = subprocess.check_output([sys.executable, __file__, '--worker', kind,
                    '--size', str(size), '--buckets', str(buckets)], text=True, timeout=120)
        row = json.loads(output)
        data['measurements'].append(row)
        with (OUT / 'measurements.json').open('w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
        print(json.dumps(row), flush=True)
    for size in {row['baskets'] for row in data['measurements']}:
        rows = [row for row in data['measurements'] if row['baskets'] == size]
        assert len({row['count_digest'] for row in rows}) == 1, size
    print('All full support-count digests match.', flush=True)


if __name__ == '__main__':
    main()

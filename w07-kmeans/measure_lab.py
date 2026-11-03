"""Supplementary, reproducible measurements; does not alter the grading harness."""
import json
import math
from pathlib import Path
import random
import statistics
import time
from datetime import datetime, timezone

import bench
import task1_kmeans as task1
from task3_fewer import NaiveKMeans, YourKMeans

OUT = Path(__file__).resolve().parent / 'out'


def recovered(labels):
    groups = [{i for i, label in enumerate(labels) if label == j} for j in set(labels)]
    return {frozenset(g) for g in groups} == {frozenset(range(a, a + 3)) for a in (0, 3, 6)}


def initializations():
    result = {}
    for method in ('random', '++'):
        runs = []
        for seed in range(40):
            labels, centroids, sse = task1.kmeans(task1.BLOBS, 3, init=method, seed=seed)
            assert (labels, centroids, sse) == task1.kmeans(task1.BLOBS, 3, init=method, seed=seed)
            runs.append(dict(seed=seed, sse=sse, recovered=recovered(labels),
                             iterations=task1.kmeans.iterations))
        values = [r['sse'] for r in runs]
        successes = sum(r['recovered'] for r in runs)
        result[method] = dict(min=min(values), max=max(values), mean=statistics.mean(values),
                              successes=successes, success_rate=successes / 40, runs=runs)
    return result


def edge_checks():
    checked = 0
    rng = random.Random(246)
    cases = [([(0.,), (1.,), (2.,)], [(0.,), (2.,)]),
             ([(0.,), (0.,), (2.,), (2.,)], [(0.,), (0.,), (100.,)]),
             ([(0.,), (1e-13,), (1.,), (1. + 1e-13,)], [(0.,), (1e-13,)]),
             ([(0.,), (3.,)], [(0.,)])]
    for _ in range(40):
        dim, n, k = rng.randrange(1, 6), rng.randrange(10, 60), rng.randrange(1, 7)
        points = [tuple(float(rng.randrange(-5, 6)) for _ in range(dim)) for _ in range(n)]
        cases.append((points, rng.sample(points, k)))
    for points, initial in cases:
        for cap in (1, 2, 50):
            base, mine = NaiveKMeans(len(initial), cap), YourKMeans(len(initial), cap)
            want = base.run(points, initial, bench.Distance())
            original = [tuple(p) for p in points]
            got = mine.run(points, initial, bench.Distance())
            assert got == want, (points, initial, cap)
            assert mine.iterations == base.iterations
            assert points == original
            checked += 1
    assert task1.assign([(1.,)], [(0.,), (2.,)]) == [0]
    try:
        task1.euclidean((1.,), (1., 2.))
    except ValueError:
        pass
    else:
        raise AssertionError('dimension mismatch must fail')
    points = [(0.,), (0.,), (1.,)]
    for init in ('random', '++'):
        labels, centroids, sse = task1.kmeans(points, 3, init=init)
        assert math.isfinite(sse) and points == [(0.,), (0.,), (1.,)]
    assert len(task1.update([(0.,), (10.,)], [0, 0], 2)) == 2
    reseeded = task1.update([(0.,), (10.,)], [0, 0], 2)
    example = dict(points=[[0], [10]], labels=[0, 0], reseeded_centroids=reseeded,
                   next_labels=task1.assign([(0.,), (10.,)], reseeded),
                   keep_old_100_centroids=[[5], [100]],
                   keep_old_next_labels=task1.assign([(0.,), (10.,)], [(5.,), (100.,)]))
    return dict(exact_baseline_cases=checked, dimension_mismatch=True, tie_check=True,
                duplicate_and_empty_cluster_checks=True, point_input_preserved=True,
                empty_cluster_example=example)


def benchmark():
    points, initial = bench.build()
    output = {}
    results = []
    for name, cls in (('baseline', NaiveKMeans), ('yours', YourKMeans)):
        distance = bench.Distance()
        algorithm = cls(bench.K)
        start = time.perf_counter()
        labels, centroids = algorithm.run(points, initial, distance)
        elapsed = time.perf_counter() - start
        row = dict(calls=distance.calls, seconds=elapsed, iterations=algorithm.iterations,
                   sse=bench.sse(points, labels, centroids))
        if name == 'yours':
            row.update(distance_stats=algorithm.distance_stats, skips=algorithm.skips,
                       iteration_calls=algorithm.iteration_calls,
                       bound_payload_bytes=algorithm.bound_bytes)
            assert sum(algorithm.distance_stats.values()) == distance.calls
            assert sum(algorithm.iteration_calls) == distance.calls
        output[name] = row
        results.append((labels, centroids))
        print(name, json.dumps(row), flush=True)
    output['identical_labels'] = results[0][0] == results[1][0]
    output['identical_centroids'] = results[0][1] == results[1][1]
    assert all((output['identical_labels'], output['identical_centroids']))
    return output


def main():
    OUT.mkdir(exist_ok=True)
    data = dict(measured_at=datetime.now(timezone.utc).isoformat(),
                initializations=initializations(), edge_checks=edge_checks())
    path = OUT / 'measurements.json'
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    data['benchmark'] = benchmark()
    path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print('All supplementary checks passed.', flush=True)


if __name__ == '__main__':
    main()

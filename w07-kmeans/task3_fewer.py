#!/usr/bin/env python3
"""Week 7 · Task 3 — The same clustering, with far fewer distances.

Textbook §7.3, and §7.1.3 for why distance is the expensive part.

`NaiveKMeans` does what the definition says: every iteration, compare every
point with every centroid. That is n x k distance computations per pass, and on
a real dataset the distance computation is almost the entire cost.

Most of that work is wasted. After the first couple of iterations, most points
do not change cluster, and most centroids barely move. The triangle inequality
lets you prove a point cannot have changed cluster **without measuring it**.

    python3 bench.py
    python3 bench.py --yours

Correctness first: your final SSE must match the baseline's. Fewer distances
with a worse clustering is not an improvement, it is a different algorithm.
"""


from array import array
import math


class NaiveKMeans:
    """Every point against every centroid, every iteration."""

    def __init__(self, k, max_iter=50):
        self.k, self.max_iter = k, max_iter

    def run(self, points, initial_centroids, distance):
        centroids = list(initial_centroids)
        labels = [None] * len(points)
        for self.iterations in range(1, self.max_iter + 1):
            changed = False
            for i, p in enumerate(points):
                best, bi = None, 0
                for j, c in enumerate(centroids):
                    d = distance(p, c)
                    if best is None or d < best - 1e-12:
                        best, bi = d, j
                if labels[i] != bi:
                    labels[i] = bi
                    changed = True
            centroids = _means(points, labels, self.k, centroids)
            if not changed:
                break
        return labels, centroids


def _means(points, labels, k, previous):
    out = []
    for j in range(k):
        group = [p for p, l in zip(points, labels) if l == j]
        if group:
            out.append(tuple(sum(v) / len(group) for v in zip(*group)))
        else:
            out.append(previous[j])
    return out


class YourKMeans:
    """Your k-means.

        __init__(k, max_iter=50)
        run(points, initial_centroids, distance) -> (labels, centroids)

    Same starting centroids, same `distance` function - which is counted. That
    counter is your score.

    The idea, from §7.3 and the triangle inequality:

        if a point is much closer to its current centroid than that centroid
        moved, and than any other centroid could have come, then it cannot have
        changed cluster, and you do not have to measure anything

    Keeping enough bookkeeping to make that test cheap, without keeping so much
    that the bookkeeping costs more than the distances, is the task.

    You may call `distance` on two centroids, and those calls are counted too -
    which is the correct accounting, since that is real work. There are k of
    them and n points, and k is much smaller than n. That asymmetry is the
    whole opening.
    """

    def __init__(self, k, max_iter=50):
        if k < 1 or max_iter < 1:
            raise ValueError("k and max_iter must be positive")
        self.k, self.max_iter = k, max_iter
        self.iterations = 0

    def run(self, points, initial_centroids, distance):
        if len(initial_centroids) != self.k:
            raise ValueError("need exactly k initial centroids")
        centroids = list(initial_centroids)
        labels = [None] * len(points)
        upper = array('d', [float('inf')]) * len(points)
        lower = array('d', [0.0]) * len(points)
        self.bound_bytes = len(points) * 2 * upper.itemsize
        self.distance_stats = dict(initial=0, reassignment=0, tightening=0,
                                   separation=0, movement=0)
        self.skips = dict(lower=0, separation=0, tightened=0)
        self.iteration_calls = []

        def measure(a, b, category):
            self.distance_stats[category] += 1
            return distance(a, b)

        def safely_below(u, bound):
            # Strict margin preserves the baseline's 1e-12 scan-order ties;
            # extra slack protects against floating-point bound updates.
            return u + 1e-10 * (1 + abs(u) + abs(bound)) < bound

        for self.iterations in range(1, self.max_iter + 1):
            before = sum(self.distance_stats.values())
            separation = [float('inf')] * self.k
            if self.iterations > 1 and self.k > 1:
                for a in range(self.k):
                    for b in range(a + 1, self.k):
                        half = measure(centroids[a], centroids[b], 'separation') / 2
                        separation[a] = min(separation[a], half)
                        separation[b] = min(separation[b], half)
            changed = False
            for i, point in enumerate(points):
                own = labels[i]
                exact_own = None
                if own is not None:
                    if safely_below(upper[i], lower[i]):
                        self.skips['lower'] += 1
                        continue
                    if safely_below(upper[i], separation[own]):
                        self.skips['separation'] += 1
                        continue
                    exact_own = measure(point, centroids[own], 'tightening')
                    upper[i] = exact_own
                    if safely_below(exact_own, max(lower[i], separation[own])):
                        self.skips['tightened'] += 1
                        continue
                category = 'initial' if own is None else 'reassignment'
                distances = [exact_own if j == own else measure(point, c, category)
                             for j, c in enumerate(centroids)]
                best, bi = None, 0
                for j, value in enumerate(distances):
                    if best is None or value < best - 1e-12:
                        best, bi = value, j
                if own != bi:
                    changed = True
                    labels[i] = bi
                upper[i] = best
                lower[i] = min((v for j, v in enumerate(distances) if j != bi),
                               default=float('inf'))
            updated = _means(points, labels, self.k, centroids)
            if changed and self.iterations < self.max_iter:
                moves = [measure(a, b, 'movement') for a, b in zip(centroids, updated)]
                max_move = max(moves)
                for i, own in enumerate(labels):
                    # Triangle inequality: u' <= u + own movement;
                    # every competing distance >= l - maximum movement.
                    upper[i] = math.nextafter(upper[i] + moves[own], math.inf)
                    lower[i] = max(0.0, math.nextafter(lower[i] - max_move, -math.inf))
            centroids = updated
            self.iteration_calls.append(sum(self.distance_stats.values()) - before)
            if not changed:
                break
        return labels, centroids

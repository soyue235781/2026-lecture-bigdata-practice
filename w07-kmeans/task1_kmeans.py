#!/usr/bin/env python3
"""Week 7 · Task 1 — k-means, and the thing that decides the answer.

Textbook §7.1 (clustering, the curse of dimensionality), §7.3 (k-means).

k-means is four lines: pick centroids, assign every point to the nearest one,
move each centroid to the mean of its points, repeat. It always converges.

It converges to a **local** optimum, and which one depends entirely on where you
started. That is not a footnote - it is the difference between a clustering that
means something and one that does not, and you can watch it happen on nine points.

    python3 task1_kmeans.py --verify
"""
import argparse, math, random

# Three obvious blobs of three points each. Any sensible clustering finds them.
BLOBS = [(0.0, 0.0), (0.2, 0.1), (0.1, 0.2),
         (8.0, 8.0), (8.2, 8.1), (8.1, 8.2),
         (0.0, 8.0), (0.2, 8.1), (0.1, 8.2)]


def euclidean(a, b):
    """Distance between two points of any dimension."""
    if len(a) != len(b):
        raise ValueError("points must have the same dimension")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def assign(points, centroids):
    """Nearest centroid for each point. Return a list of centroid indices.

    Ties go to the lower index, so that everybody's answer is the same.
    """
    if not centroids:
        raise ValueError("at least one centroid is required")
    return [min(range(len(centroids)), key=lambda j: euclidean(p, centroids[j]))
            for p in points]


def update(points, labels, k):
    """Move each centroid to the mean of its points.

    An empty cluster has no mean. Decide what you do - and say so, because the
    choice changes the result and there is more than one defensible answer.
    """
    if not points or k < 1 or len(labels) != len(points):
        raise ValueError("nonempty points, positive k and one label per point required")
    if any(label not in range(k) for label in labels):
        raise ValueError("label outside cluster range")
    dim = len(points[0])
    if any(len(p) != dim for p in points):
        raise ValueError("points must have the same dimension")
    groups = [[p for p, label in zip(points, labels) if label == j] for j in range(k)]
    centroids = [tuple(sum(v) / len(group) for v in zip(*group)) if group else None
                 for group in groups]
    # No previous centres are available in this interface. Reseed each empty
    # centre at the point farthest from the already populated/reseeded centres.
    available = [c for c in centroids if c is not None]
    for j, centre in enumerate(centroids):
        if centre is None:
            point = max(points, key=lambda p: min(euclidean(p, c) for c in available))
            centroids[j] = tuple(point)
            available.append(centroids[j])
    return centroids


def kmeans(points, k, init="random", seed=246, max_iter=100):
    """Run to convergence. Return (labels, centroids, sse).

    `sse` is the sum over points of the squared distance to their own centroid.
    It is what k-means minimises, and it is how you compare two runs.

    `init` is either:
        "random"   pick k points at random as the starting centroids
        "++"       k-means++ (§7.3.2): pick the first at random, then pick each
                   next one with probability proportional to the squared distance
                   to the nearest centroid already chosen

    Set `kmeans.iterations` to how many passes you used.
    """
    kmeans.iterations = 0
    if not points or not 1 <= k <= len(points) or max_iter < 1:
        raise ValueError("require nonempty points, 1 <= k <= n and positive max_iter")
    if init not in ('random', '++'):
        raise ValueError("init must be random or ++")
    dim = len(points[0])
    if any(len(p) != dim for p in points):
        raise ValueError("points must have the same dimension")
    rng = random.Random(seed)
    if init == 'random':
        indices = rng.sample(range(len(points)), k)
    else:
        indices = [rng.randrange(len(points))]
        nearest = [float('inf')] * len(points)
        while len(indices) < k:
            last = points[indices[-1]]
            for i, point in enumerate(points):
                nearest[i] = min(nearest[i], euclidean(point, last) ** 2)
            total = sum(nearest)
            if total == 0:
                chosen = next(i for i in range(len(points)) if i not in indices)
            else:
                target = rng.random() * total
                cumulative = 0.0
                chosen = None
                for i, weight in enumerate(nearest):
                    cumulative += weight
                    if weight > 0 and cumulative > target:
                        chosen = i
                        break
                if chosen is None:  # rounding at the cumulative endpoint
                    chosen = next(i for i in reversed(range(len(points))) if nearest[i] > 0)
            indices.append(chosen)
    centroids = [tuple(points[i]) for i in indices]
    labels = None
    for iteration in range(1, max_iter + 1):
        new_labels = assign(points, centroids)
        centroids = update(points, new_labels, k)
        kmeans.iterations = iteration
        if new_labels == labels:
            break
        labels = new_labels
    return labels, centroids, sse_of(points, labels, centroids)


def sse_of(points, labels, centroids):
    """Sum of squared distances from each point to its assigned centroid."""
    if len(points) != len(labels):
        raise ValueError("one label per point required")
    return sum(euclidean(point, centroids[label]) ** 2
               for point, label in zip(points, labels))


# ------------------------------------------------------------------- harness
def verify():
    fails = 0

    def check(label, ok, detail=""):
        nonlocal fails
        print(f"  {'ok  ' if ok else 'FAIL'}  {label:<50} {detail}")
        fails += not ok

    try:
        check("distance in 2d", abs(euclidean((0, 0), (3, 4)) - 5) < 1e-9)
        check("distance in 5d",
              abs(euclidean((0,) * 5, (1,) * 5) - math.sqrt(5)) < 1e-9)
    except NotImplementedError:
        print("  euclidean is still a stub"); return 1

    try:
        labels, cents, sse = kmeans(BLOBS, 3, init="++", seed=1)
    except NotImplementedError:
        print("  kmeans is still a stub"); return 1

    groups = {}
    for p, l in zip(BLOBS, labels):
        groups.setdefault(l, []).append(p)
    check("three clusters of three", sorted(len(g) for g in groups.values()) == [3, 3, 3],
          sorted(len(g) for g in groups.values()))
    check("the three blobs were recovered",
          all(max(q[0] for q in g) - min(q[0] for q in g) < 1 and
              max(q[1] for q in g) - min(q[1] for q in g) < 1
              for g in groups.values()))
    check("sse is small when clusters are right", sse < 1.0, f"sse {sse:.4f}")

    # Bad luck with random starts should sometimes be visibly worse.
    randoms = [kmeans(BLOBS, 3, init="random", seed=s)[2] for s in range(40)]
    plusplus = [kmeans(BLOBS, 3, init="++", seed=s)[2] for s in range(40)]
    check("random init sometimes lands badly", max(randoms) > min(randoms) * 5,
          f"sse from {min(randoms):.3f} to {max(randoms):.3f}")
    check("k-means++ is more reliable than random",
          sum(plusplus) / len(plusplus) <= sum(randoms) / len(randoms),
          f"mean sse: ++ {sum(plusplus) / len(plusplus):.3f} vs "
          f"random {sum(randoms) / len(randoms):.3f}")

    print(f"\n  {'all ok' if not fails else str(fails) + ' failed'}")
    return 1 if fails else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    a = p.parse_args()
    raise SystemExit(verify() if a.verify else p.print_help())

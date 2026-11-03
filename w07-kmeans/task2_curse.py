#!/usr/bin/env python3
"""Week 7 · Task 2 — Watch distance stop meaning anything.

Textbook §7.1.3, the curse of dimensionality.

In two dimensions "nearest" is obvious. In two hundred, every point is roughly
the same distance from every other point, and a method built on "nearest" has
nothing left to stand on.

That is usually stated as a fact to accept. Here you measure it, on your own
machine, and find the dimension where it starts to bite for **your** data size.

    python3 task2_curse.py --dims 2,5,10,20,50,100,200
    python3 task2_curse.py --dims 500,1000 --points 2000

The contrast ratio is the number to watch.
"""
import argparse, json, math, os, platform, random, time
import ctypes
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    info = {"platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "python": platform.python_version(), "logical_cpus": os.cpu_count(),
            "environment": "User local Windows PC, Codex restricted execution process"}
    if os.name == 'nt':
        class Memory(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ('ram', 'available', 'page', 'available_page', 'virtual', 'available_virtual', 'extended')]
        memory = Memory()
        memory.length = ctypes.sizeof(memory)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            info['ram_bytes'] = memory.ram
            info['available_ram_bytes'] = memory.available
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
            info['processor'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
    return info


def euclid(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def sample_distances(n, dim, pairs, seed=246):
    if n < 2 or dim < 1 or pairs < 1:
        raise ValueError("require n >= 2, dim >= 1 and pairs >= 1")
    rng = random.Random(seed + dim)
    pts = [tuple(rng.random() for _ in range(dim)) for _ in range(n)]
    ds = []
    while len(ds) < pairs:
        i, j = rng.randrange(n), rng.randrange(n)
        if i != j:
            ds.append(euclid(pts[i], pts[j]))
    return ds


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dims", default="2,5,10,20,50,100,200")
    p.add_argument("--points", type=int, default=1000)
    p.add_argument("--pairs", type=int, default=20000)
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    path = os.path.join(OUT, 'curse.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as stream:
            prior = json.load(stream)
    else:
        prior = {'runs': []}
    prior['machine'] = machine()
    for dim in [int(x) for x in a.dims.split(",")]:
        t0 = time.perf_counter()
        ds = sample_distances(a.points, dim, a.pairs)
        elapsed = time.perf_counter() - t0
        lo, hi = min(ds), max(ds)
        mean = sum(ds) / len(ds)
        var = sum((d - mean) ** 2 for d in ds) / len(ds)
        row = {"dim": dim, "points": a.points, "pairs": len(ds),
               "min": lo, "max": hi, "mean": mean,
               "stdev": math.sqrt(var),
               "contrast": (hi - lo) / lo if lo else None,
               "relative_stdev": math.sqrt(var) / mean if mean else None,
               "seconds": elapsed, "seed": 246, "effective_seed": 246 + dim,
               "requested_pairs": a.pairs,
               "measured_at": datetime.now(timezone.utc).isoformat(),
               "sampling": "with replacement; self-index pairs rejected until requested count"}
        prior['runs'].append(row)
        with open(path + '.tmp', 'w', encoding='utf-8') as stream:
            json.dump(prior, stream, indent=2)
        os.replace(path + '.tmp', path)
        print(f"  dim {dim:>5}   mean {mean:>7.3f}   min {lo:>7.3f}   "
              f"max {hi:>7.3f}   contrast {row['contrast']:>7.3f}   "
              f"rel.sd {row['relative_stdev']:>6.3f}")

    path = os.path.join(OUT, "curse.json")
    print(f"\n  -> out/curse.json  ({len(prior['runs'])} measurement(s))")


if __name__ == "__main__":
    main()

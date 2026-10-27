#!/usr/bin/env python3
"""Week 6 · Task 2 — Lower the threshold until your machine says no.

Textbook §6.1, §6.2.

Support is a knob, and turning it down is how you find the interesting rules.
It is also how you run out of memory, and where that happens is a fact about
your laptop rather than about the algorithm.

    python3 task2_explosion.py --supports 400,200,100,50,25
    python3 task2_explosion.py --supports 12,6            # careful

Lower the threshold until something gives. Write down where and what.
"""
import argparse, json, os, platform, time, tracemalloc
import ctypes
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine():
    info = {"platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "python": platform.python_version(), "logical_cpus": os.cpu_count(),
            "environment": "Local Windows desktop, Codex restricted execution process",
            "background_programs": "Not fully visible from the restricted process; no claim of an idle machine"}
    if os.name == 'nt':
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ('total_physical', 'available_physical', 'total_page', 'available_page',
                 'total_virtual', 'available_virtual', 'extended')]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            info['ram_bytes'] = status.total_physical
            info['available_ram_bytes'] = status.available_physical
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                info['processor'] = winreg.QueryValueEx(key, 'ProcessorNameString')[0].strip()
        except OSError:
            pass
    return info


def save(data):
    path = os.path.join(OUT, 'explosion.json')
    temporary = path + '.tmp'
    with open(temporary, 'w', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
    os.replace(temporary, path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--supports", default="400,200,100,50,25")
    a = p.parse_args()
    os.makedirs(OUT, exist_ok=True)

    import bench
    from task3_pcy import PlainApriori
    baskets = bench.build()

    path = os.path.join(OUT, 'explosion.json')
    if os.path.exists(path):
        with open(path, encoding='utf-8') as stream:
            prior = json.load(stream)
    else:
        prior = {'runs': []}
    prior['machine'] = machine()
    prior['conditions'] = {'baskets': bench.BASKETS, 'items': bench.ITEMS,
                           'seed': bench.SEED, 'memory': 'tracemalloc peak during algorithm; excludes prebuilt baskets',
                           'timing': 'tracemalloc enabled; not comparable to untraced bench timings'}
    for support in [int(x) for x in a.supports.split(",")]:
        algo = PlainApriori(support)
        tracemalloc.start()
        t0 = time.perf_counter()
        try:
            pairs = algo.run(baskets)
        except (MemoryError, KeyboardInterrupt) as error:
            prior.setdefault('failures', []).append({
                'support': support, 'status': type(error).__name__,
                'seconds': time.perf_counter() - t0,
                'peak_bytes': tracemalloc.get_traced_memory()[1],
                'measured_at': datetime.now(timezone.utc).isoformat()})
            tracemalloc.stop()
            save(prior)
            raise
        elapsed = time.perf_counter() - t0
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        row = {"support": support, "frequent_pairs": len(pairs),
               "peak_counters": algo.peak_counters, "seconds": elapsed,
               "peak_bytes": peak_bytes, 'status': 'success',
               'measured_at': datetime.now(timezone.utc).isoformat()}
        prior['runs'].append(row)
        save(prior)
        del pairs
        print(f"  support {support:>5}   pairs {row['frequent_pairs']:>7,}   "
              f"counters {algo.peak_counters:>10,}   "
              f"{elapsed:>7.2f}s   {peak_bytes / 1e6:>8.1f} MB")

    path = os.path.join(OUT, "explosion.json")
    print(f"\n  -> out/explosion.json  ({len(prior['runs'])} run(s))")
    print("  Keep halving the support until it is unbearable. Record where.")


if __name__ == "__main__":
    main()

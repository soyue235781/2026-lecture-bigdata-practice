#!/usr/bin/env python3
"""Week 3 · Task 2 — Find the crossover on your own machine.

Textbook §3.4.

Everybody knows brute force is quadratic and LSH is not. That is not the
interesting question. The interesting question is **where, on the machine in
front of you, does it start to matter** - and that answer is yours alone. It
depends on your CPU, your memory, and how big your shingle sets are.

This script gives you the timing loop. The two methods are yours: import them
from Task 1 and Task 3.

    python3 task2_crossover.py --sizes 500,1000,2000,4000
    python3 task2_crossover.py --sizes 8000,16000          # keep going

Write down where it hurts. That is the deliverable.
"""
import argparse, json, math, os, platform, random, time, tracemalloc
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine(background="Codex desktop and Python active; other applications not audited"):
    processor = platform.processor() or platform.machine()
    ram_bytes = None
    if os.name == "nt":
        import ctypes
        import winreg

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in
                ("total_phys", "avail_phys", "total_page", "avail_page",
                 "total_virtual", "avail_virtual", "avail_extended")]

        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            ram_bytes = status.total_phys
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                processor = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    elif hasattr(os, "sysconf"):
        try:
            ram_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (OSError, ValueError):
            pass
    return {
        "platform": platform.platform(),
        "processor": processor,
        "ram_bytes": ram_bytes,
        "hostname": platform.node(),
        "python": platform.python_version(),
        "background": background,
    }


def timed(fn, docs, similarity):
    """Time without tracing, then measure peak allocations in a separate call."""
    import bench

    t0 = time.perf_counter()
    result = fn(docs, similarity)
    elapsed = time.perf_counter() - t0
    # A fresh counter keeps the second, instrumented call out of the score.
    tracemalloc.start()
    try:
        fn(docs, bench.Counter())
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, elapsed, peak


def build_docs(n):
    """Keep the harness's shingle sizes and duplicate fraction as n grows."""
    import bench

    rng = random.Random(bench.SEED)
    clones = min(n - 1, round(n * bench.PLANTED / (bench.N_DOCS + bench.PLANTED)))
    base = n - clones
    docs = [set(rng.sample(range(bench.VOCAB), bench.SHINGLES)) for _ in range(base)]
    for _ in range(clones):
        clone = set(docs[rng.randrange(base)])
        for _ in range(rng.randint(4, 14)):
            clone.discard(rng.choice(list(clone)))
            clone.add(rng.randrange(bench.VOCAB))
        docs.append(clone)
    rng.shuffle(docs)
    return docs


def write_curve(data):
    """Derive the table and doubling check only from saved measurements."""
    # The latest measurement for a size represents that point on the curve.
    latest = {row["n"]: row for row in data["runs"]}
    rows = [latest[n] for n in sorted(latest)]
    info = data["machine"]
    ram = info.get("ram_bytes")
    lines = ["# Task 2 — local measurement curve", "",
             f"- CPU: {info['processor']}",
             f"- RAM: {ram / 2**30:.2f} GiB" if ram else "- RAM: TODO (detection unavailable)",
             f"- OS / Python: {info['platform']} / {info['python']}",
             f"- Other activity: {info['background']}",
             "- Time excludes input generation. Memory is a separate tracemalloc run; "
             "peak means Python allocations during find(), excluding the existing docs "
             "and interpreter, not total process RAM.", "",
             "| n | brute s | LSH s | brute comparisons | LSH comparisons | brute peak MiB | LSH peak MiB |",
             "|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['n']} | {row['brute_s']:.6f} | {row['lsh_s']:.6f} | "
                     f"{row['brute_calls']} | {row['lsh_calls']} | "
                     f"{row['brute_peak_bytes'] / 2**20:.3f} | {row['lsh_peak_bytes'] / 2**20:.3f} |")
    lines.extend(["", "## Quadratic check", "",
                  "| n → 2n | measured brute time ratio | expected comparison ratio | fitted exponent log2(time ratio) |",
                  "|---|---:|---:|---:|"])
    ratios = []
    for row in rows:
        doubled = latest.get(2 * row["n"])
        if doubled and row["brute_s"] > 0:
            ratio = doubled["brute_s"] / row["brute_s"]
            ratios.append(ratio)
            expected = doubled["brute_calls"] / row["brute_calls"]
            lines.append(f"| {row['n']} → {doubled['n']} | {ratio:.3f} | "
                         f"{expected:.3f} | {math.log2(ratio):.3f} |")
    if ratios:
        lines.extend(["", f"Mean doubling time ratio: {sum(ratios) / len(ratios):.3f} "
                      "(ideal quadratic: 4). Read the individual ratios above for deviations."])
    lines.extend(["", "## Crossover and practical limit", ""])
    crossings = [(left["n"], right["n"]) for left, right in zip(rows, rows[1:])
                 if left["brute_s"] < left["lsh_s"]
                 and right["brute_s"] >= right["lsh_s"]]
    if crossings:
        lines.append("Observed brute→LSH crossover bracket(s): " +
                     ", ".join(f"{lo} < n <= {hi}" for lo, hi in crossings) +
                     ". The exact crossing needs intermediate sizes.")
    elif rows and all(row["brute_s"] >= row["lsh_s"] for row in rows):
        lines.append(f"LSH is already faster at the smallest measured n={rows[0]['n']}; "
                     "measure smaller sizes to bracket the crossover.")
    else:
        lines.append("No brute→LSH crossover bracket yet; measure larger sizes.")
    lines.append("At small n, LSH pays to index shingles, compute 128 hash minima, "
                 "and build 32 band bucket tables before verifying candidates; "
                 "brute force starts comparing immediately.")
    limits = data.get("limits", [])
    if limits:
        for limit in limits:
            lines.append(f"- n={limit['n']}: {limit['reason']}")
    else:
        lines.append("- TODO: continue until waiting or memory pressure becomes unpleasant; record that n.")
    if rows:
        largest = rows[-1]
        lines.append(f"- Largest n={largest['n']}: brute peak "
                     f"{largest['brute_peak_bytes'] / 2**20:.3f} MiB; LSH peak "
                     f"{largest['lsh_peak_bytes'] / 2**20:.3f} MiB (traced allocations).")
        span = rows[-1]["n"] / rows[0]["n"]
        lines.append(f"- Coverage: {len(rows)} distinct sizes, {span:g}× span; "
                     f"A1 {'met' if len(rows) >= 5 and span >= 16 else 'needs more sizes'}.")
    with open(os.path.join(OUT, "curve.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="250,500,1000,2000",
                   help="comma-separated document counts to try")
    p.add_argument("--threshold", type=float, default=0.6)
    p.add_argument("--background", default="Codex desktop and Python active; other applications not audited",
                   help="describe other running applications")
    p.add_argument("--unpleasant-n", type=int, help="size at which waiting or memory became unpleasant")
    p.add_argument("--unpleasant-reason", help="describe the observed waiting or memory pressure")
    a = p.parse_args()
    try:
        sizes = [int(x) for x in a.sizes.split(",")]
    except ValueError:
        p.error("sizes must be comma-separated integers")
    if any(n < 2 for n in sizes):
        p.error("every size must be at least 2")
    if not 0 < a.threshold <= 1:
        p.error("threshold must be in (0, 1]")
    if (a.unpleasant_n is None) != (a.unpleasant_reason is None):
        p.error("use --unpleasant-n and --unpleasant-reason together")
    os.makedirs(OUT, exist_ok=True)

    import bench
    from task3_scale import BruteForce, YourFinder

    path = os.path.join(OUT, "crossover.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            prior = json.load(f)
    else:
        prior = {"runs": [], "limits": []}
    info = machine(a.background)
    config = {"threshold": a.threshold, "seed": bench.SEED,
              "shingles": bench.SHINGLES, "vocab": bench.VOCAB,
              "generator": "scaled-harness-v1", "hashes": 128, "bands": 32,
              "timing": "untraced; separate traced memory pass"}
    if prior["runs"]:
        if any(prior.get("machine", {}).get(key) != info[key]
               for key in ("platform", "processor", "ram_bytes", "hostname", "python")):
            p.error("existing measurements belong to another machine; preserve/move out/crossover.json first")
        if prior.get("config") != config:
            p.error("existing measurements use a different configuration; preserve/move out/crossover.json first")
    prior["machine"] = info
    prior["config"] = config
    prior.setdefault("limits", [])
    if a.unpleasant_n is not None:
        prior["limits"].append({"n": a.unpleasant_n, "reason": a.unpleasant_reason})

    for n in sizes:
        docs = build_docs(n)
        print(f"  measuring n={len(docs)} (time pass + memory pass per method)", flush=True)
        measurement_start = time.perf_counter()
        sim = bench.Counter()
        _, t_brute, m_brute = timed(BruteForce(a.threshold).find, docs, sim)
        c_brute = sim.calls

        row = {"n": n, "brute_s": t_brute, "brute_calls": c_brute,
               "brute_peak_bytes": m_brute, "actual_docs": len(docs),
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "background": a.background}

        sim2 = bench.Counter()
        _, t_lsh, m_lsh = timed(YourFinder(a.threshold).find, docs, sim2)
        row.update({"lsh_s": t_lsh, "lsh_calls": sim2.calls,
                    "lsh_peak_bytes": m_lsh,
                    "measurement_s": time.perf_counter() - measurement_start})
        if max(t_brute, t_lsh) >= 60:
            prior["limits"].append({"n": n, "reason":
                                    f"single untraced find() reached {max(t_brute, t_lsh):.2f}s"})
        elif row["measurement_s"] >= 60:
            prior["limits"].append({"n": n, "reason":
                                    f"full measurement including tracing took {row['measurement_s']:.2f}s; "
                                    "this is instrumentation waiting, not a 60s find()"})
        prior["runs"].append(row)
        # Save each completed size so an interrupted larger run loses no data.
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            # ASCII escapes also work with the harness's Windows text encoding.
            json.dump(prior, f, indent=2, ensure_ascii=True)
        os.replace(temporary, path)
        write_curve(prior)
        line = f"  n={n:>6}  brute {t_brute:>8.2f}s  {c_brute:>12,} cmp"
        if "lsh_s" in row:
            line += f"   |  lsh {row['lsh_s']:>7.2f}s  {row['lsh_calls']:>9,} cmp"
        print(line, flush=True)

    print(f"\n  -> out/crossover.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until something becomes unpleasant. Record where.")


if __name__ == "__main__":
    main()

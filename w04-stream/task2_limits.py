#!/usr/bin/env python3
"""Week 4 · Task 2 — Find the size where exact stops being possible.

Textbook §4.1 (the stream model), §4.4, §4.5.

Sketches exist because the exact answer does not fit. That sentence is easy to
agree with and hard to feel, so this task makes you watch it happen on your own
machine: hold every distinct item in a set, keep raising the stream size, and
record where your laptop stops coping.

    python3 task2_limits.py --sizes 100000,400000,1600000
    python3 task2_limits.py --sizes 6400000            # keep going

Your numbers will not match anybody else's. That is the point.
"""
import argparse, json, os, platform, time, tracemalloc
from datetime import datetime, timezone


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def machine(background="Codex desktop and measurement Python active; other apps not audited"):
    processor = platform.processor() or platform.machine()
    ram_bytes = available_bytes = None
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
            ram_bytes, available_bytes = status.total_phys, status.avail_phys
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                processor = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    elif hasattr(os, "sysconf"):
        try:
            ram_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            available_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_AVPHYS_PAGES")
        except (OSError, ValueError):
            pass
    return {"platform": platform.platform(), "processor": processor,
            "ram_bytes": ram_bytes, "available_ram_bytes": available_bytes,
            "python": platform.python_version(), "hostname": platform.node(),
            "environment": ("local Windows PC, executed through Codex desktop" if os.name == "nt"
                            else "non-Windows host; not asserted to be the user's local PC"),
            "background": background}


def stream(n, distinct_ratio=0.4, seed=246):
    """A stream of n items with about n*distinct_ratio distinct values."""
    import random
    rng = random.Random(seed)
    span = max(1, int(n * distinct_ratio))
    for _ in range(n):
        yield f"key-{rng.randrange(span)}"


def exact_distinct(n):
    """The honest answer: hold every distinct item."""
    def count(size):
        seen = set()
        for x in stream(size):
            seen.add(x)
        return len(seen)
    return measured(count, n)


def measured(fn, n):
    """Separate timing and tracing so allocation tracking does not distort time."""
    t0 = time.perf_counter()
    result = fn(n)
    elapsed = time.perf_counter() - t0
    tracemalloc.start()
    try:
        repeated = fn(n)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    if repeated != result:
        raise RuntimeError("measurement passes were not reproducible")
    return result, elapsed, peak


def write_report(data):
    """Build the report from saved measurements; never invent a hardware limit."""
    latest = {row["n"]: row for row in data["runs"]}
    rows = [latest[n] for n in sorted(latest)]
    info = data["machine"]
    ram = info.get("ram_bytes")
    lines = ["# Task 2: Exact distinct counting and Flajolet-Martin", "",
             "## Environment and method", "",
             f"- CPU: {info['processor']}",
             f"- RAM: {ram / 2**30:.2f} GiB" if ram else "- RAM: not detected",
             f"- OS / Python / NumPy: {info['platform']} / {info['python']} / {data['config']['numpy']}",
             f"- Host: {info['hostname']}; {info['environment']}",
             f"- Other activity: {info['background']}",
             "- Fixed seed 246; n generated strings sampled from a key space of size 0.4n. "
             "True distinct count is measured, not assumed to equal 0.4n.",
             "- FM uses 64 trailing-zero maxima and median of group means in log space. "
             "Fixed batches of at most 256 integer hashes accelerate arithmetic; the stream is not stored.",
             "- Each method has an untraced timing pass and a separate traced memory pass. "
             "Both include lazy input generation. Imports are completed before measurement. "
             "Peak includes allocations made during the call, including stream and FM scratch buffers; "
             "it excludes the existing interpreter/modules and is not total process RSS.", "",
             "## Results", "",
             "| n | true distinct | exact s | exact peak MiB | FM s | FM peak MiB | FM estimate | estimate / truth |",
             "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(f"| {row['n']:,} | {row['true_distinct']:,} | {row['exact_s']:.3f} | "
                     f"{row['exact_peak_bytes'] / 2**20:.3f} | {row['fm_s']:.3f} | "
                     f"{row['fm_peak_bytes'] / 2**20:.3f} | {row['fm_estimate']:,.1f} | {row['fm_ratio']:.4f} |")
    lines.extend(["", "## Growth and accuracy", "",
                  "| n change | n multiplier | distinct multiplier | exact memory multiplier | FM memory multiplier |",
                  "|---|---:|---:|---:|---:|"])
    for left, right in zip(rows, rows[1:]):
        lines.append(f"| {left['n']:,} -> {right['n']:,} | {right['n'] / left['n']:.3f} | "
                     f"{right['true_distinct'] / left['true_distinct']:.3f} | "
                     f"{right['exact_peak_bytes'] / left['exact_peak_bytes']:.3f} | "
                     f"{right['fm_peak_bytes'] / left['fm_peak_bytes']:.3f} |")
    if len(rows) > 1:
        first, last = rows[0], rows[-1]
        span = last["n"] / first["n"]
        lines.extend(["", f"Coverage: {len(rows)} distinct sizes and a {span:g}x range; "
                      f"A1 {'met' if len(rows) >= 4 and span >= 16 else 'needs more measurements'}.",
                      f"Across this range, exact peak grows {last['exact_peak_bytes'] / first['exact_peak_bytes']:.3f}x "
                      f"and FM peak grows {last['fm_peak_bytes'] / first['fm_peak_bytes']:.3f}x.",
                      "Exact retains distinct strings and a resizable set table; set resize thresholds "
                      "make memory growth uneven. FM retains a fixed number of registers and bounded scratch buffers.",
                      f"FM accuracy ratios range from {min(r['fm_ratio'] for r in rows):.4f} to "
                      f"{max(r['fm_ratio'] for r in rows):.4f}. Fixed hash count does not promise "
                      "that relative error improves with longer streams; compare each observed ratio above.",
                      "FM saves space but hashes each item 64 ways, so memory savings do not imply faster execution."])
    lines.extend(["", "## Practical limit and limitations", ""])
    if data.get("limits"):
        lines.extend(f"- n={limit['n']:,}: {limit['reason']}" for limit in data["limits"])
    else:
        lines.append("The exact method did not reach a recorded time or memory limit in this measured range. "
                     "This is not evidence that exact counting scales without limit.")
    if rows:
        last = rows[-1]
        lines.append(f"Largest measured n={last['n']:,}: exact {last['exact_s']:.3f}s and "
                     f"{last['exact_peak_bytes'] / 2**20:.3f} MiB; FM {last['fm_s']:.3f}s and "
                     f"{last['fm_peak_bytes'] / 2**20:.3f} MiB.")
    lines.extend(["Further sizes such as 25,000,000 are needed to locate an exact-counting hardware limit. "
                  "The script estimates memory risk before running larger sizes rather than exhausting RAM.",
                  "These are single measurements on one synthetic workload with 40% key-space size. "
                  "Different distinct fractions, longer strings, other running apps, or repeated timing trials "
                  "could change the practical limit. FM estimates are probabilistic, not exact counts."])
    with open(os.path.join(OUT, "limits.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="100000,400000,1600000")
    p.add_argument("--background", default="Codex desktop and measurement Python active; other apps not audited")
    p.add_argument("--unpleasant-n", type=int)
    p.add_argument("--unpleasant-reason")
    a = p.parse_args()
    try:
        sizes = [int(x) for x in a.sizes.split(",")]
    except ValueError:
        p.error("sizes must be comma-separated integers")
    if any(n <= 0 for n in sizes):
        p.error("every size must be positive")
    if (a.unpleasant_n is None) != (a.unpleasant_reason is None):
        p.error("provide both --unpleasant-n and --unpleasant-reason")
    os.makedirs(OUT, exist_ok=True)

    import numpy as np
    from task1_sketches import flajolet_martin

    path = os.path.join(OUT, "limits.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            prior = json.load(f)
    else:
        prior = {"runs": [], "limits": []}
    info = machine(a.background)
    config = {"seed": 246, "distinct_ratio": 0.4, "n_hashes": 64,
              "fm_combination": "median of group mean R, exponentiated",
              "batch_size": 256, "numpy": np.__version__,
              "measurement": "untraced timing and separate tracemalloc pass"}
    if prior["runs"] and (prior.get("config") != config or any(
            prior.get("machine", {}).get(key) != info[key]
            for key in ("platform", "processor", "ram_bytes", "python", "hostname"))):
        p.error("existing data uses another machine/configuration; preserve/move limits.json first")
    prior["machine"], prior["config"] = info, config
    prior.setdefault("limits", [])
    if a.unpleasant_n is not None:
        prior["limits"].append({"n": a.unpleasant_n, "reason": a.unpleasant_reason})

    for n in sizes:
        available = machine(a.background).get("available_ram_bytes")
        # Conservative planning allowance, not a reported memory measurement.
        if available and n * 0.4 * 160 > available / 4:
            p.error(f"n={n} could consume over 25% of available RAM; stopped before allocation")
        print(f"  measuring n={n:,}: exact timing + memory", flush=True)
        start = time.perf_counter()
        true, t_exact, m_exact = exact_distinct(n)
        row = {"n": n, "true_distinct": true, "exact_s": t_exact,
               "exact_peak_bytes": m_exact,
               "timestamp_utc": datetime.now(timezone.utc).isoformat(),
               "available_ram_bytes_before": available, "background": a.background}
        print(f"    exact: {t_exact:.3f}s, {m_exact / 2**20:.3f} MiB; measuring FM", flush=True)
        est, t_fm, m_fm = measured(lambda size: flajolet_martin(stream(size)), n)
        row.update({"fm_estimate": est, "fm_s": t_fm, "fm_peak_bytes": m_fm,
                    "fm_ratio": est / true, "measurement_s": time.perf_counter() - start})
        if t_exact >= 60:
            prior["limits"].append({"n": n, "reason": f"exact timing pass took {t_exact:.3f}s (over one minute)"})
        if info.get("ram_bytes") and m_exact > info["ram_bytes"] / 10:
            prior["limits"].append({"n": n, "reason": "traced exact peak exceeded 10% of physical RAM"})
        prior["runs"].append(row)
        # Save completed sizes before starting another potentially long run.
        temporary = path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as f:
            json.dump(prior, f, indent=2, ensure_ascii=True)
        os.replace(temporary, path)
        write_report(prior)
        line = (f"  n={n:>10,}  distinct {true:>9,}   exact {t_exact:>7.2f}s "
                f"{m_exact / 1e6:>8.1f} MB")
        if "fm_s" in row:
            line += (f"   |  fm {row['fm_s']:>7.2f}s {row['fm_peak_bytes'] / 1e6:>6.2f} MB"
                     f"  {row['fm_ratio']:.2f}x")
        print(line, flush=True)
    print(f"\n  -> out/limits.json  ({len(prior['runs'])} measurement(s))")
    print("  Keep raising --sizes until the exact version is unbearable. "
          "Record where, and what ran out.")


if __name__ == "__main__":
    main()

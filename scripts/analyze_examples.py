#!/usr/bin/env python3
"""Розбір ГОТОВИХ кліпів клієнта — щоб витягнути правила відбору й монтажу.

Для кожного файлу: тривалість, точки внутрішніх різів (скільки фрагментів
склеєно), пословний транскрипт, паузи між фразами і розкладка по бітах.

    python3 pipeline/analyze_examples.py "~/Desktop/examples"/*.mp4 -o work/examples.json
"""
import argparse, glob, json, os, re, subprocess, sys

def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height,codec_type",
         "-of", "json", path], capture_output=True, text=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s.get("codec_type") == "video"), {})
    return float(d["format"]["duration"]), v.get("width"), v.get("height")

def video_band(path):
    """Де в 9:16 кадрі живе саме відео (без чорних полів і шапки)."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-ss", "3", "-t", "3",
                        "-i", path, "-vf", "cropdetect=limit=24:round=2",
                        "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r)
    if not m:
        return None
    w, h, x, y = map(int, m[-1])
    return w, h, x, y

def cuts(path, band, thr=5.0):
    """Внутрішні різи: scdet по смузі самого відео, щоб шапка не заважала."""
    vf = f"scdet=threshold={thr}"
    if band:
        w, h, x, y = band
        # беремо середню третину смуги — там обличчя, там і видно склейку
        vf = f"crop={w}:{max(80,h//2)}:{x}:{y + h//4},{vf}"
    r = subprocess.run(["ffmpeg", "-nostdin", "-hide_banner", "-i", path,
                        "-vf", vf, "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return [round(float(t), 2) for t in re.findall(r"lavfi\.scd\.time:\s*([0-9.]+)", r)]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("-o", "--out", default="work/examples.json")
    ap.add_argument("--model", default="medium", help="whisper: small | medium | large-v3")
    a = ap.parse_args()

    paths = []
    for f in a.files:
        paths += sorted(glob.glob(os.path.expanduser(f)))
    paths = [p for p in paths if p.lower().endswith((".mp4", ".mov", ".m4v"))]
    if not paths:
        sys.exit("файлів не знайдено")

    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count())

    results = []
    for p in paths:
        dur, w, h = probe(p)
        band = video_band(p)
        cut_pts = cuts(p, band)
        segs, _ = model.transcribe(p, language="en", word_timestamps=True,
                                   vad_filter=True, beam_size=5)
        segs = [{"s": round(x.start, 2), "e": round(x.end, 2), "t": x.text.strip()}
                for x in segs]

        # паузи ≥0.6с — межі смислових бітів
        beats = [round(segs[i + 1]["s"] - segs[i]["e"], 2) for i in range(len(segs) - 1)]
        pauses = [(segs[i]["e"], beats[i]) for i in range(len(beats)) if beats[i] >= 0.6]

        name = os.path.basename(p)
        print(f"\n{'='*70}\n{name}   {dur:.1f}с   {w}x{h}")
        print(f"фрагментів: {len(cut_pts)+1}" + (f"  (різи: {cut_pts})" if cut_pts else "  (суцільний)"))
        if pauses:
            print("паузи ≥0.6с: " + ", ".join(f"{t:.1f}с/{g:.1f}" for t, g in pauses[:12]))
        print("-" * 70)
        for x in segs:
            mark = " ✂" if any(abs(x["s"] - c) < 1.0 for c in cut_pts) else "  "
            print(f"{mark}[{x['s']:6.2f} → {x['e']:6.2f}] {x['t']}")

        results.append({"file": name, "path": p, "duration": round(dur, 2),
                        "size": f"{w}x{h}", "video_band": band,
                        "cut_points": cut_pts, "fragments": len(cut_pts) + 1,
                        "pauses": pauses, "segments": segs,
                        "text": " ".join(x["t"] for x in segs)})

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(results, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(f"\n\n{len(results)} кліпів → {a.out}")

if __name__ == "__main__":
    main()

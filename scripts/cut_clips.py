#!/usr/bin/env python3
"""Крок 3 — нарізка за ПРИТЯГНУТИМ планом (виходом snap_clips.py).

Кожен clip = склейка своїх фрагментів у порядку плану.
Завжди перекодування (точний різ), concat через demuxer.

    python3 pipeline/cut_clips.py work/plan.snapped.json --video "source.mp4" --out clips_out
    ... --only 03,07      тільки ці кліпи
    ... --vertical        9:16 720x1280 (відео по центру, чорні поля)
"""
import argparse, json, os, re, shutil, subprocess, sys

def slug(s, n=60):
    s = re.sub(r"[^\w\s-]", "", str(s or "")).strip()
    s = re.sub(r"[\s_]+", "-", s).lower()
    return s[:n].strip("-") or "clip"

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr[-2000:] + "\n")
        raise SystemExit(f"ffmpeg впав: {' '.join(cmd[:8])}…")

VF_VERTICAL = ("scale=720:-2:flags=lanczos,"
               "pad=720:1280:(ow-iw)/2:(oh-ih)/2:black,setsar=1")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--video", default=None, help="перекрити шлях до вихідного відео")
    ap.add_argument("--out", default="clips_out")
    ap.add_argument("--temp", default="work/frag")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--preset", default="veryfast")
    ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--only", default=None, help="через кому: 01,04,09")
    ap.add_argument("--keep-temp", action="store_true")
    a = ap.parse_args()

    data = json.load(open(a.plan))
    clips = data["clips"] if isinstance(data, dict) else data
    only = {x.strip() for x in a.only.split(",")} if a.only else None

    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.temp, exist_ok=True)
    made = []

    for n, clip in enumerate(clips, 1):
        cid = str(clip.get("id", f"{n:02d}"))
        if only and cid not in only and str(n) not in only:
            continue
        src = a.video or clip.get("source") or data.get("video")
        if not src or not os.path.exists(src):
            raise SystemExit(f"немає вихідного відео: {src}")

        frags = [f for f in clip["fragments"] if "error" not in f.get("snap", {})]
        if not frags:
            print(f"Clip {cid}: пропуск — жодного придатного фрагмента"); continue

        name = f"{cid}_{slug(clip.get('title'))}.mp4"
        parts = []
        for fi, f in enumerate(frags, 1):
            s, e = f["snap"]["start"], f["snap"]["end"]
            part = os.path.join(a.temp, f"{cid}_{fi:02d}.mp4")
            cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error",
                   "-ss", f"{s:.3f}", "-to", f"{e:.3f}", "-i", src,
                   "-c:v", "libx264", "-preset", a.preset, "-crf", str(a.crf),
                   "-pix_fmt", "yuv420p", "-r", "30",
                   "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
            if a.vertical:
                cmd += ["-vf", VF_VERTICAL]
            cmd.append(part)
            run(cmd)
            parts.append(part)

        dst = os.path.join(a.out, name)
        if len(parts) == 1:
            shutil.copyfile(parts[0], dst)
        else:
            lst = os.path.join(a.temp, f"{cid}_concat.txt")
            with open(lst, "w") as fh:
                for p in parts:
                    fh.write(f"file '{os.path.abspath(p)}'\n")
            run(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat",
                 "-safe", "0", "-i", lst, "-c", "copy", dst])

        size = os.path.getsize(dst) / 1e6
        print(f"Clip {cid}: {len(parts)} фрагм. · {clip.get('total_duration','?')}с · "
              f"{size:.1f} MB → {dst}")
        made.append(dst)

    if not a.keep_temp:
        shutil.rmtree(a.temp, ignore_errors=True)
    print(f"\nготово: {len(made)} кліпів у {a.out}/")

if __name__ == "__main__":
    main()

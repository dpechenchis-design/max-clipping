#!/usr/bin/env python3
"""ФАЗА 1, вартовий — чи кожна цитата плану реально є в транскрипті.

Захищає від головної помилки на етапі відбору: переказати думку своїми словами
замість дослівної цитати. Тоді на фазі 2 snap не знайде цих слів у відео.
Заодно підтягує таймкоди з транскрипту, якщо в плані їх нема або вони брехливі.

    python3 validate_plan.py clips_plan.json transcript.txt [--fix]

--fix впише знайдені таймкоди назад у план.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textmatch import tokenize, align, parse_tc, fmt_tc
from parse_transcript import parse

def build_index(blocks):
    """Транскрипт → суцільний потік токенів + таймкод для кожного."""
    toks, times = [], []
    for b in blocks:
        t0 = b["t"]
        bt = tokenize(b["text"])
        # рівномірно розкладаємо час блоку по його словах — точність ±довжина блоку,
        # цього досить, щоб задати вікно пошуку для фази 2
        span = ((b["end"] - t0) if (b["end"] and t0 is not None) else None)
        for k, tok in enumerate(bt):
            toks.append(tok)
            if t0 is None:
                times.append(None)
            elif span:
                times.append(t0 + span * k / max(1, len(bt)))
            else:
                times.append(t0)
    return toks, times

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("transcript")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--min-coverage", type=float, default=0.85)
    a = ap.parse_args()

    data = json.load(open(a.plan))
    clips = data["clips"] if isinstance(data, dict) else data
    blocks = parse(a.transcript)
    toks, times = build_index(blocks)
    print(f"транскрипт: {len(blocks)} блоків, {len(toks)} слів, "
          f"{sum(1 for t in times if t is not None)} з таймкодом\n")

    problems = 0
    for n, clip in enumerate(clips, 1):
        cid = str(clip.get("id", f"{n:02d}"))
        print(f"Clip {cid} · {clip.get('type','?')} · {clip.get('title','')}")
        for fi, frag in enumerate(clip.get("fragments", []), 1):
            text = (frag.get("text") or "").strip()
            if not text:
                print(f"   frag {fi}: ✗ порожній text — фаза 2 не зможе його знайти")
                problems += 1
                continue
            tgt = tokenize(text)
            r = align(toks, tgt)
            if r is None:
                print(f"   frag {fi}: ✗ у транскрипті такого нема")
                problems += 1
                continue
            i0, i1, cov, matched, _ = r
            t_start = next((times[k] for k in range(i0, min(i1 + 1, len(times))) if times[k] is not None), None)
            t_end = next((times[k] for k in range(min(i1, len(times) - 1), i0 - 1, -1) if times[k] is not None), None)
            mark = "✓" if cov >= a.min_coverage else "⚠"
            if cov < a.min_coverage:
                problems += 1
            print(f"   frag {fi}: {mark} збіг {cov*100:3.0f}%  {len(tgt)} слів  "
                  f"транскрипт {fmt_tc(t_start)} → {fmt_tc(t_end)}")
            if cov < a.min_coverage:
                heard = " ".join(toks[i0:i1 + 1])
                print(f"            план : {' '.join(tgt)[:110]}")
                print(f"            текст: {heard[:110]}")
                print(f"            → цитуй дослівно з транскрипту, не переказуй")
            hint = parse_tc(frag.get("start"))
            if hint is not None and t_start is not None and abs(hint - t_start) > 30:
                print(f"            ⚠ таймкод плану {fmt_tc(hint)} vs транскрипт "
                      f"{fmt_tc(t_start)} — розбіжність {abs(hint-t_start):.0f}с")
                problems += 1
            if a.fix and t_start is not None:
                frag["start"], frag["end"] = fmt_tc(t_start), fmt_tc(t_end)

    print(f"\n{len(clips)} кліпів · {problems} проблем")
    if a.fix:
        json.dump(data, open(a.plan, "w"), indent=2, ensure_ascii=False)
        print(f"→ таймкоди з транскрипту вписано в {a.plan}")
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()

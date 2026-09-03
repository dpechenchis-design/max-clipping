#!/usr/bin/env python3
"""Крок 2 — притягнути таймкоди плану до РЕАЛЬНИХ меж слів.

Таймкоди у плані (від клієнта, з ютубу, з ока) майже завжди зсунуті на 1-3 с.
Тут ми беремо ТЕКСТ фрагмента, знаходимо його у пословному транскрипті і
ставимо різ рівно на початок першого слова / кінець останнього.

    python3 pipeline/snap_clips.py plan.json work/video.words.json -o work/plan.snapped.json

Опції: --window 120 (пошук ±120с від підказки), --lead 0.35, --tail 0.45
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textmatch import tokenize, word_tokens, align, similarity, parse_tc, fmt_tc

def snap_fragment(frag, words, toks, tok2word, window, lead, tail, dur):
    """Повертає dict з точними межами + діагностикою."""
    hint_s = parse_tc(frag.get("start"))
    hint_e = parse_tc(frag.get("end"))
    text = (frag.get("text") or "").strip()
    res = {"hint_start": hint_s, "hint_end": hint_e}

    # --- межі вікна пошуку ---
    if hint_s is not None:
        lo_t, hi_t = hint_s - window, (hint_e if hint_e is not None else hint_s + 60) + window
    else:
        lo_t, hi_t = 0.0, dur
    lo = next((k for k, wi in enumerate(tok2word) if words[wi]["end"] >= lo_t), 0)
    hi = next((k for k in range(len(tok2word) - 1, -1, -1)
               if words[tok2word[k]]["start"] <= hi_t), len(tok2word) - 1)
    hi = max(hi, lo)

    if not text:
        # немає тексту — просто не ріжемо посеред слова
        if hint_s is None:
            res["error"] = "ні тексту, ні таймкоду"
            return res
        i = min(range(lo, hi + 1), key=lambda k: abs(words[tok2word[k]]["start"] - hint_s))
        j = min(range(lo, hi + 1), key=lambda k: abs(words[tok2word[k]]["end"] - (hint_e or hint_s)))
        res.update(mode="timecode-only", coverage=None)
    else:
        tgt = tokenize(text)
        a = align(toks[lo:hi + 1], tgt)
        if a is None:
            res["error"] = "текст не знайдено у вікні пошуку"
            return res
        i0, i1, cov, matched, _ = a
        i, j = lo + i0, lo + i1
        res.update(mode="text-anchored", coverage=round(cov, 3),
                   words_expected=len(tgt), words_matched=matched)

    i, j = max(0, i), min(len(tok2word) - 1, max(i, j))
    w_first, w_last = words[tok2word[i]], words[tok2word[j]]

    # скільки тиші довкола — щоб знати, чи безпечно ставити буфер
    prev_end = words[tok2word[i] - 1]["end"] if tok2word[i] > 0 else 0.0
    next_start = (words[tok2word[j] + 1]["start"]
                  if tok2word[j] + 1 < len(words) else dur)
    gap_before = round(w_first["start"] - prev_end, 3)
    gap_after = round(next_start - w_last["end"], 3)

    start = max(0.0, w_first["start"] - min(lead, max(gap_before, 0.05)))
    end = min(dur, w_last["end"] + min(tail, max(gap_after, 0.05)))

    heard = " ".join(w["w"] for w in words[tok2word[i]:tok2word[j] + 1])
    res.update(
        start=round(start, 3), end=round(end, 3), duration=round(end - start, 3),
        start_tc=fmt_tc(start), end_tc=fmt_tc(end),
        first_word=w_first["w"], last_word=w_last["w"],
        gap_before=gap_before, gap_after=gap_after,
        drift_start=(round(start - hint_s, 2) if hint_s is not None else None),
        drift_end=(round(end - hint_e, 2) if hint_e is not None else None),
        heard=heard,
    )
    warn = []
    if res.get("coverage") is not None and res["coverage"] < 0.8:
        warn.append(f"збіг лише {res['coverage']*100:.0f}% — перевір текст фрагмента")
    if gap_before < 0.12:
        warn.append(f"перед першим словом тиші {gap_before:.2f}с — впритул до попередньої фрази")
    if gap_after < 0.12:
        warn.append(f"після останнього слова тиші {gap_after:.2f}с — обірве наступне слово")
    if res["duration"] < 1.0:
        warn.append("фрагмент коротший за секунду")
    if hint_s is not None and abs(res["drift_start"] or 0) > 15:
        warn.append(f"зсув від таймкоду плану {res['drift_start']:+.0f}с — можливо не той шматок")
    res["warnings"] = warn
    return res

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan"); ap.add_argument("words")
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--window", type=float, default=120.0, help="пошук ±N с від таймкоду плану")
    ap.add_argument("--lead", type=float, default=0.35, help="повітря перед першим словом")
    ap.add_argument("--tail", type=float, default=0.45, help="повітря після останнього слова")
    a = ap.parse_args()

    plan = json.load(open(a.plan))
    if isinstance(plan, dict):
        plan = plan.get("clips", [])
    W = json.load(open(a.words))
    words, dur = W["words"], W["duration"]
    toks, tok2word = word_tokens(words)

    out_clips, bad = [], 0
    for n, clip in enumerate(plan, 1):
        frags = clip.get("fragments") or [{k: clip.get(k) for k in ("start", "end", "text")}]
        snapped = []
        print(f"\nClip {clip.get('id', n)} — {clip.get('title','')}")
        for fi, frag in enumerate(frags, 1):
            s = snap_fragment(frag, words, toks, tok2word, a.window, a.lead, a.tail, dur)
            snapped.append({**frag, "snap": s})
            if "error" in s:
                bad += 1
                print(f"   frag {fi}: ✗ {s['error']}")
                continue
            cov = f"{s['coverage']*100:3.0f}%" if s.get("coverage") is not None else " tc "
            dr = f"{s['drift_start']:+.1f}с" if s.get("drift_start") is not None else "  —  "
            print(f"   frag {fi}: {s['start_tc']} → {s['end_tc']}  ({s['duration']:5.1f}с) "
                  f"збіг {cov}  зсув {dr}  «{s['first_word']} … {s['last_word']}»")
            for w in s["warnings"]:
                bad += 1
                print(f"            ⚠ {w}")
        total = sum(f["snap"].get("duration", 0) for f in snapped)
        print(f"   → разом {total:.1f}с")
        out_clips.append({**clip, "fragments": snapped, "total_duration": round(total, 2)})

    out = a.out or a.plan.replace(".json", ".snapped.json")
    json.dump({"video": W.get("video"), "clips": out_clips}, open(out, "w"),
              indent=2, ensure_ascii=False)
    print(f"\n{len(out_clips)} кліпів · {bad} зауважень\n→ {out}")

if __name__ == "__main__":
    main()

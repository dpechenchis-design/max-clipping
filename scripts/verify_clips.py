#!/usr/bin/env python3
"""Крок 4 — КОНТРОЛЬ ПО СЛОВАХ. Перетранскрибовує нарізані кліпи і звіряє з планом.

Це та перевірка, заради якої все й робиться: не «таймкод збігається»,
а «у готовому файлі реально звучать ті слова, які мали звучати,
перше слово не з'їдене, останнє не обірване, зайвого не причепилось».

    python3 pipeline/verify_clips.py work/plan.snapped.json --clips clips_out
    ... --model small.en --fix   (--fix перезаписує план з виправленими межами)
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textmatch import tokenize, similarity

OK, WARN, FAIL = "OK", "WARN", "FAIL"

def expected_text(clip):
    parts = []
    for f in clip["fragments"]:
        t = (f.get("text") or "").strip()
        if not t:
            t = f.get("snap", {}).get("heard", "")
        parts.append(t)
    return " ".join(parts).strip()

def check(exp_toks, got_toks, edge=4):
    """Порівняння очікуваного і почутого — по opcodes, а не по рівності крайніх слів.

    Принципова різниця трьох випадків на краю кліпа:
      delete  — слова були в плані, у файлі їх нема   → різ з'їв, треба буфер
      insert  — у файлі є зайві слова                 → зачепили сусідню фразу
      replace — слово почулось інакше                 → whisper недочув, різ правильний
    """
    from difflib import SequenceMatcher
    issues, soft = [], []
    sim = similarity(exp_toks, got_toks)
    if not exp_toks or not got_toks:
        return FAIL, ["порожній транскрипт"], {"similarity": 0.0, "head_words_lost": -1,
                "tail_words_lost": -1, "words_expected": len(exp_toks),
                "words_heard": len(got_toks), "head_extra": 0, "tail_extra": 0}

    ops = SequenceMatcher(None, exp_toks, got_toks, autojunk=False).get_opcodes()
    head_lost = tail_lost = head_extra = tail_extra = 0

    tag, i1, i2, j1, j2 = ops[0]
    if tag == "delete":
        head_lost = i2 - i1
    elif tag == "insert":
        head_extra = j2 - j1
    elif tag == "replace":
        soft.append(f"перше слово почулось як «{' '.join(got_toks[j1:j2][:3])}» "
                    f"замість «{' '.join(exp_toks[i1:i2][:3])}»")

    tag, i1, i2, j1, j2 = ops[-1]
    if tag == "delete":
        tail_lost = i2 - i1
    elif tag == "insert":
        tail_extra = j2 - j1
    elif tag == "replace":
        soft.append(f"останнє слово почулось як «{' '.join(got_toks[j1:j2][-3:])}» "
                    f"замість «{' '.join(exp_toks[i1:i2][-3:])}»")

    if head_lost:
        issues.append(f"з'їдено {head_lost} перших слів "
                      f"({' '.join(exp_toks[:head_lost])}) — збільш --lead")
    if tail_lost:
        issues.append(f"обірвано {tail_lost} останніх слів "
                      f"({' '.join(exp_toks[-tail_lost:])}) — збільш --tail")
    if head_extra > 2:
        issues.append(f"на початку {head_extra} зайвих слів "
                      f"({' '.join(got_toks[:head_extra])}) — зачепило попередню фразу")
    if tail_extra > 2:
        issues.append(f"в кінці {tail_extra} зайвих слів "
                      f"({' '.join(got_toks[-tail_extra:])}) — зачепило наступну фразу")
    if sim < 0.75:
        issues.append(f"текст збігається лише на {sim*100:.0f}%")

    # перечуте слово саме по собі кліп не ламає — це зауваження, не помилка
    status = FAIL if (sim < 0.6 or head_lost > 3 or tail_lost > 3) else \
             (WARN if issues else OK)
    return status, issues + ([] if issues else soft), {
        "similarity": round(sim, 3), "head_words_lost": head_lost,
        "tail_words_lost": tail_lost, "head_extra": head_extra, "tail_extra": tail_extra,
        "words_expected": len(exp_toks), "words_heard": len(got_toks),
        "misheard": soft}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--clips", default="clips_out")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--out", default="work/verify_report.json")
    ap.add_argument("--fix", action="store_true",
                    help="дописати виправлені межі у план (start-=, end+=) і зберегти")
    a = ap.parse_args()

    data = json.load(open(a.plan))
    clips = data["clips"] if isinstance(data, dict) else data

    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count())

    files = {f.split("_")[0]: f for f in sorted(os.listdir(a.clips)) if f.endswith(".mp4")}
    report, counts = [], {OK: 0, WARN: 0, FAIL: 0}

    for n, clip in enumerate(clips, 1):
        cid = str(clip.get("id", f"{n:02d}"))
        fn = files.get(cid)
        if not fn:
            print(f"Clip {cid}: ✗ файлу немає у {a.clips}/"); continue
        path = os.path.join(a.clips, fn)

        segs, info = model.transcribe(path, language="en", vad_filter=True, beam_size=5)
        got = " ".join(s.text.strip() for s in segs).strip()
        exp = expected_text(clip)
        status, issues, m = check(tokenize(exp), tokenize(got))
        counts[status] += 1

        mark = {OK: "✓", WARN: "⚠", FAIL: "✗"}[status]
        print(f"{mark} Clip {cid} · {info.duration:5.1f}с · збіг {m['similarity']*100:3.0f}% · {fn}")
        for i in issues:
            print(f"      → {i}")
        if status != OK:
            print(f"      план : …{' '.join(tokenize(exp)[:8])} … {' '.join(tokenize(exp)[-6:])}")
            print(f"      факт : …{' '.join(tokenize(got)[:8])} … {' '.join(tokenize(got)[-6:])}")

        if a.fix and clip["fragments"]:
            if m["head_words_lost"] and m["head_words_lost"] > 0:
                clip["fragments"][0]["snap"]["start"] = round(
                    max(0, clip["fragments"][0]["snap"]["start"] - 0.25 * m["head_words_lost"]), 3)
            if m["tail_words_lost"] and m["tail_words_lost"] > 0:
                clip["fragments"][-1]["snap"]["end"] = round(
                    clip["fragments"][-1]["snap"]["end"] + 0.25 * m["tail_words_lost"], 3)

        report.append({"id": cid, "file": fn, "status": status, "issues": issues,
                       "duration": round(info.duration, 2), "expected": exp, "heard": got, **m})

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(f"\n✓ {counts[OK]}   ⚠ {counts[WARN]}   ✗ {counts[FAIL]}\n→ {a.out}")

    if a.fix:
        json.dump(data if isinstance(data, dict) else clips, open(a.plan, "w"),
                  indent=2, ensure_ascii=False)
        print(f"→ межі виправлено у {a.plan} — перенаріж cut_clips.py і прогони перевірку ще раз")
    sys.exit(1 if counts[FAIL] else 0)

if __name__ == "__main__":
    main()

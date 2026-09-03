#!/usr/bin/env python3
"""Крок 1 — транскрипція вихідного відео з ТАЙМКОДАМИ НА КОЖНЕ СЛОВО.

Це фундамент усього пайплайну. Далі ми ніколи не довіряємо таймкодам з
транскрипту клієнта — ми знаходимо потрібні СЛОВА у цьому файлі і беремо
їхні реальні межі.

    python3 pipeline/transcribe_source.py "video.mp4" [--model medium.en] [--lang en]

Результат: work/<video>.words.json
"""
import argparse, json, os, sys, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--model", default="medium.en",
                    help="tiny.en | base.en | small.en | medium.en | large-v3 (за замовчуванням medium.en)")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    args = ap.parse_args()

    if not os.path.exists(args.video):
        sys.exit(f"немає файлу: {args.video}")

    from faster_whisper import WhisperModel

    base = os.path.splitext(os.path.basename(args.video))[0]
    out = args.out or os.path.join("work", f"{base}.words.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    print(f"модель {args.model} (CPU int8, {args.workers} threads)…", flush=True)
    model = WhisperModel(args.model, device="cpu", compute_type="int8",
                         cpu_threads=args.workers)

    t0 = time.time()
    segments, info = model.transcribe(
        args.video,
        language=args.lang,
        word_timestamps=True,          # ← головне
        vad_filter=True,               # ріже тишу, точніші межі слів
        vad_parameters={"min_silence_duration_ms": 300},
        beam_size=5,
        condition_on_previous_text=False,  # менше галюцинацій на довгих відео
    )

    words, segs = [], []
    total = info.duration
    for seg in segments:
        segs.append({"start": round(seg.start, 3), "end": round(seg.end, 3),
                     "text": seg.text.strip()})
        for w in (seg.words or []):
            words.append({"w": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3), "p": round(w.probability, 3)})
        done = seg.end
        print(f"\r  {done/60:6.1f} / {total/60:.1f} хв  ({done/total*100:5.1f}%)  "
              f"{len(words)} слів", end="", flush=True)

    print(f"\nготово за {(time.time()-t0)/60:.1f} хв · {len(words)} слів · {len(segs)} сегментів")

    with open(out, "w") as f:
        json.dump({"video": os.path.basename(args.video),
                   "duration": round(total, 3),
                   "model": args.model,
                   "segments": segs,
                   "words": words}, f, ensure_ascii=False)
    print(f"→ {out}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Розбір довгого транскрипту в нормалізований вигляд: (таймкод, спікер, текст).

Ковтає найпоширеніші формати:
    [00:12:04] текст                     [00:12:04 → 00:12:30] текст
    00:12:04  текст                      12:04 текст
    Max (00:12:04): текст                Max 00:12:04
    SRT (номер / 00:00:12,040 --> …)     WebVTT
"""
import re, sys, os

TC = r"(\d{1,2}:\d{2}(?::\d{2})?(?:[.,]\d{1,3})?)"
PATTERNS = [
    re.compile(r"^\s*\[?" + TC + r"\s*(?:[-–—>→]+\s*" + TC + r")?\s*\]?\s*[:\-–]?\s*(.*)$"),
    re.compile(r"^\s*(?P<spk>[\w .'\-]{1,40}?)\s*[\(\[]" + TC + r"[\)\]]\s*:?\s*(.*)$"),
    re.compile(r"^\s*(?P<spk>[\w .'\-]{1,40}?)\s+" + TC + r"\s*:?\s*(.*)$"),
]
SRT_ARROW = re.compile(TC + r"\s*-->\s*" + TC)

def to_sec(tc):
    if tc is None:
        return None
    tc = tc.replace(",", ".")
    p = [float(x) for x in tc.split(":")]
    return p[0] * 60 + p[1] if len(p) == 2 else p[0] * 3600 + p[1] * 60 + p[2]

def parse(path):
    """→ [{'t': сек, 'end': сек|None, 'speaker': str|None, 'text': str}]"""
    raw = open(path, encoding="utf-8", errors="replace").read()
    raw = raw.replace("﻿", "")
    lines = raw.splitlines()
    blocks, pending = [], None

    for line in lines:
        s = line.strip()
        if not s or s.startswith("WEBVTT") or re.fullmatch(r"\d+", s):
            continue
        m = SRT_ARROW.search(s)                       # SRT / VTT
        if m:
            pending = {"t": to_sec(m.group(1)), "end": to_sec(m.group(2)),
                       "speaker": None, "text": ""}
            blocks.append(pending)
            continue
        hit = None
        for pat in PATTERNS:
            m = pat.match(s)
            if m and m.lastindex and m.group(1):
                hit = m
                break
        if hit:
            g = hit.groupdict()
            gs = hit.groups()
            tcs = [x for x in gs if x and re.fullmatch(TC, x)]
            text = hit.group(hit.lastindex) if hit.lastindex else ""
            pending = {"t": to_sec(tcs[0]) if tcs else None,
                       "end": to_sec(tcs[1]) if len(tcs) > 1 else None,
                       "speaker": (g.get("spk") or "").strip() or None,
                       "text": text.strip()}
            blocks.append(pending)
        elif pending is not None:
            pending["text"] = (pending["text"] + " " + s).strip()
        else:
            blocks.append({"t": None, "end": None, "speaker": None, "text": s})
            pending = blocks[-1]

    return [b for b in blocks if b["text"]]

if __name__ == "__main__":
    bl = parse(sys.argv[1])
    have = sum(1 for b in bl if b["t"] is not None)
    print(f"{len(bl)} блоків, з таймкодом {have}, слів {sum(len(b['text'].split()) for b in bl)}")
    for b in bl[:8]:
        tc = f"{int(b['t']//60):02d}:{b['t']%60:05.2f}" if b["t"] is not None else "  —  "
        print(f"  [{tc}] {(b['speaker'] or '')+': ' if b['speaker'] else ''}{b['text'][:80]}")

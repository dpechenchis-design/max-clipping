#!/usr/bin/env python3
"""Спільна логіка: нормалізація тексту і вирівнювання цитати на потік слів.

Whisper пише "COVID-19", "gonna", "$5", клієнт пише "COVID 19", "going to", "5 dollars".
Тому порівнюємо не рядки, а нормалізовані токени, і не на рівність, а через
difflib — воно витримує пропущені/зайві/переплутані слова.
"""
import re, unicodedata
from difflib import SequenceMatcher

_NUM = {
    "zero":"0","one":"1","two":"2","three":"3","four":"4","five":"5","six":"6",
    "seven":"7","eight":"8","nine":"9","ten":"10",
}
_FILLER = {"uh", "um", "mm", "hmm", "ah", "er", "eh"}

def norm_token(w: str) -> str:
    w = unicodedata.normalize("NFKD", w).lower()
    w = re.sub(r"[^a-z0-9']", "", w)      # геть пунктуацію, лишаємо апостроф
    w = w.replace("'", "")                 # don't → dont
    return _NUM.get(w, w)

def tokenize(text: str, drop_filler: bool = True):
    """Рядок → список нормалізованих токенів (порожні відкидаємо)."""
    out = []
    for raw in re.split(r"\s+", text or ""):
        t = norm_token(raw)
        if not t:
            continue
        if drop_filler and t in _FILLER:
            continue
        out.append(t)
    return out

def word_tokens(words, drop_filler: bool = True):
    """Список слів whisper → (токени, індекси на оригінальний масив)."""
    toks, idx = [], []
    for i, w in enumerate(words):
        t = norm_token(w["w"])
        if not t:
            continue
        if drop_filler and t in _FILLER:
            continue
        toks.append(t)
        idx.append(i)
    return toks, idx

def align(src_tokens, tgt_tokens):
    """Де в src_tokens лежить tgt_tokens.

    Повертає (i_start, i_end, coverage, matched, blocks) в індексах src_tokens.
    coverage = частка токенів цитати, які реально знайшлись (0..1).
    Індекси екстраполюються, якщо перше/останнє слово цитати не збіглося —
    саме тому кліп не з'їдає перше слово.
    """
    if not src_tokens or not tgt_tokens:
        return None
    sm = SequenceMatcher(None, src_tokens, tgt_tokens, autojunk=False)
    blocks = [b for b in sm.get_matching_blocks() if b.size > 0]
    if not blocks:
        return None
    matched = sum(b.size for b in blocks)
    first, last = blocks[0], blocks[-1]
    i_start = first.a - first.b                       # позиція токена №0 цитати
    i_end = (last.a + last.size - 1) + (len(tgt_tokens) - 1 - (last.b + last.size - 1))
    i_start = max(0, min(i_start, len(src_tokens) - 1))
    i_end = max(i_start, min(i_end, len(src_tokens) - 1))
    return i_start, i_end, matched / len(tgt_tokens), matched, blocks

def similarity(a_tokens, b_tokens) -> float:
    """0..1, наскільки два шматки тексту це одне й те саме."""
    if not a_tokens and not b_tokens:
        return 1.0
    if not a_tokens or not b_tokens:
        return 0.0
    return SequenceMatcher(None, a_tokens, b_tokens, autojunk=False).ratio()

def parse_tc(tc):
    """'01:02:03.5' | '02:03' | 123.4 → секунди (float)."""
    if tc is None:
        return None
    if isinstance(tc, (int, float)):
        return float(tc)
    tc = str(tc).strip().replace(",", ".")
    parts = tc.split(":")
    try:
        parts = [float(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

def fmt_tc(sec):
    if sec is None:
        return "—"
    sec = max(0.0, float(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

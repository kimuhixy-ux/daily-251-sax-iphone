#!/usr/bin/env python3
"""
build_xml_score.py
-------------------
MusicXML/mxlファイルからメロディー(実音)とコードネームを抽出し、
アプリの「XMLインポート」カテゴリ用のフレーズJSONを1曲分生成する。

常にtoSoundingPitch()で実音(コンサートピッチ)に変換してから読む。
ギター譜などは記譜が実音より1オクターブ高いなど、楽器ごとの記譜習慣で
ずれることがあるため。

使い方:
    python3 build_xml_score.py 入力ファイル.musicxml --title "曲名"

出力:
    data/xml_scores/<id>.json を書き出し、
    data/xml_scores/manifest.json にエントリを追加/更新する
    (同じidが既にあれば上書き)。これにより、以後XMLファイルを
    追加するたびにこのスクリプトを実行するだけでアプリに反映される。
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from music21 import converter, note, harmony
except ImportError:
    print("music21が見つかりません。次のコマンドでインストールしてください:", file=sys.stderr)
    print("  pip3 install music21", file=sys.stderr)
    sys.exit(1)

DATA_DIR = Path(__file__).parent / "data" / "xml_scores"


def slugify(text):
    s = re.sub(r"[^0-9A-Za-z一-龠ぁ-んァ-ヶー]+", "_", text).strip("_")
    return s or "score"


def build_bars(sounding_part, total_bars, base_measure):
    chords = list(sounding_part.recurse().getElementsByClass(harmony.ChordSymbol))
    bars = [[] for _ in range(total_bars)]
    for c in chords:
        idx = c.measureNumber - base_measure
        if 0 <= idx < total_bars:
            bars[idx].append(c.figure)
    # コード記号がない小節は、リードシートの慣習に合わせて直前のコードを引き継ぐ
    last = None
    for b in bars:
        if not b and last:
            b.append(last)
        elif b:
            last = b[-1]
    return bars


def build_notes(sounding_part, base_measure):
    notes = []
    for n in sounding_part.recurse().notesAndRests:
        entry = {
            "barIndex": n.measureNumber - base_measure,
            "beatInBar": float(n.offset),
            "duration": float(n.quarterLength),
        }
        if isinstance(n, note.Note):
            entry["letter"] = n.pitch.step
            entry["octave"] = n.pitch.octave
            entry["accidental"] = int(round(n.pitch.alter))
        elif isinstance(n, note.Rest):
            entry["rest"] = True
        else:
            continue  # 和音(Chord)はメロディー抽出の対象外
        notes.append(entry)
    return notes


def main():
    ap = argparse.ArgumentParser(description="MusicXMLからXMLインポートカテゴリ用フレーズを生成")
    ap.add_argument("input", help="MusicXMLファイル(.musicxml / .xml / .mxl)")
    ap.add_argument("--title", required=True, help="アプリ上に表示する曲名")
    ap.add_argument("--id", help="内部ID(省略時はtitleから自動生成)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ファイルが見つかりません: {in_path}", file=sys.stderr)
        sys.exit(1)

    score = converter.parse(str(in_path))
    part = score.parts[0]
    instr = part.getInstrument(returnDefault=True)
    sounding = part.toSoundingPitch() if instr.transposition else part

    measure_numbers = [m.measureNumber for m in sounding.recurse().getElementsByClass("Measure")]
    base_measure = min(measure_numbers)
    total_bars = max(measure_numbers) - base_measure + 1

    notes = build_notes(sounding, base_measure)
    bars = build_bars(sounding, total_bars, base_measure)
    chords_display = " | ".join(b[0] if b else "?" for b in bars) if any(bars) else "(コード情報なし)"

    result_id = args.id or slugify(args.title)
    result = {
        "id": result_id,
        "title": args.title,
        "key": "C",
        "bars": bars,
        "chordsDisplay": chords_display,
        "notes": notes,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{result_id}.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    manifest_path = DATA_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    manifest = [m for m in manifest if m["id"] != result_id]
    manifest.append({"id": result_id, "title": args.title, "file": out_path.name})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"生成: {out_path}")
    print(f"  小節数={total_bars}, 音符・休符数={len(notes)}")
    print(f"  manifest更新: {manifest_path}")


if __name__ == "__main__":
    main()

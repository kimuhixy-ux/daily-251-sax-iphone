#!/usr/bin/env python3
"""
parse_musicxml.py
-----------------
MusicXMLファイルをmusic21で機械的に解析し、
音符情報(オクターブを含む)を正確なJSONとして出力するスクリプト。

Claude CodeにMusicXMLを直接読ませず、必ずこのスクリプトの
JSON出力を渡すことで、オクターブの読み違いを防ぐ。

使い方:
    python3 parse_musicxml.py 入力ファイル.musicxml
    python3 parse_musicxml.py 入力ファイル.xml -o 出力先.json

出力される情報(音符ごと):
    - measure        : 小節番号
    - offset         : 小節内での位置(拍、4分音符=1.0)
    - written_pitch  : 記譜上の音名+オクターブ(例 "A4")
    - sounding_pitch : 実音の音名+オクターブ(移調楽器を実音に変換)
    - midi           : 実音のMIDIノート番号(オクターブ確認用の決定的な値)
    - duration       : 音価(4分音符=1.0)
    - type           : note / chord / rest
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from music21 import converter, note, chord
except ImportError:
    print("music21が見つかりません。次のコマンドでインストールしてください:", file=sys.stderr)
    print("  pip3 install music21", file=sys.stderr)
    sys.exit(1)


def pitch_info(p):
    """music21のPitchオブジェクトから名前・オクターブ・MIDI番号を取り出す"""
    return {
        "name": p.nameWithOctave,   # 例 "A4"(MusicXML標準: 中央ド=C4)
        "step": p.step,             # 例 "A"
        "octave": p.octave,         # 例 4
        "midi": p.midi,             # 例 69(決定的な値。オクターブ検証に使う)
    }


def parse_file(path):
    score = converter.parse(str(path))

    result = {
        "source_file": str(path),
        "octave_convention": "MusicXML標準(中央ド=C4)。ヤマハ式表示とは1オクターブずれるので注意。",
        "parts": [],
    }

    for part in score.parts:
        instr = part.getInstrument(returnDefault=True)
        transpose = instr.transposition  # 移調楽器ならIntervalが入る(例: アルトサックス)

        part_data = {
            "part_name": part.partName or instr.instrumentName or "unknown",
            "instrument": instr.instrumentName,
            "is_transposing": transpose is not None,
            "transposition": str(transpose) if transpose else None,
            "notes": [],
        }

        # written(記譜)とsounding(実音)の両方を用意
        written = part
        sounding = part.toSoundingPitch() if transpose else part

        w_notes = list(written.recurse().notesAndRests)
        s_notes = list(sounding.recurse().notesAndRests)

        for w, s in zip(w_notes, s_notes):
            entry = {
                "measure": w.measureNumber,
                "offset": float(w.offset),
                "duration": float(w.quarterLength),
            }
            if isinstance(w, note.Note):
                entry["type"] = "note"
                entry["written"] = pitch_info(w.pitch)
                entry["sounding"] = pitch_info(s.pitch)
            elif isinstance(w, chord.Chord):
                entry["type"] = "chord"
                entry["written"] = [pitch_info(p) for p in w.pitches]
                entry["sounding"] = [pitch_info(p) for p in s.pitches]
            else:  # 休符
                entry["type"] = "rest"
            part_data["notes"].append(entry)

        part_data["note_count"] = len(part_data["notes"])
        result["parts"].append(part_data)

    return result


def main():
    ap = argparse.ArgumentParser(description="MusicXMLを解析してJSONを出力")
    ap.add_argument("input", help="MusicXMLファイル(.musicxml / .xml / .mxl)")
    ap.add_argument("-o", "--output", help="出力JSONファイル(省略時は 入力名.json)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"ファイルが見つかりません: {in_path}", file=sys.stderr)
        sys.exit(1)

    data = parse_file(in_path)

    out_path = Path(args.output) if args.output else in_path.with_suffix(".json")
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(p["note_count"] for p in data["parts"])
    print(f"解析完了: {in_path.name}")
    print(f"  パート数: {len(data['parts'])}, 音符・休符数: {total}")
    for p in data["parts"]:
        t = f"(移調楽器: {p['transposition']})" if p["is_transposing"] else ""
        print(f"  - {p['part_name']} {t}")
    print(f"  出力: {out_path}")


if __name__ == "__main__":
    main()

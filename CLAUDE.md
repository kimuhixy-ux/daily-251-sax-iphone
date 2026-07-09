# MusicXML処理のルール(CLAUDE.mdに追記する内容)

## 必須ワークフロー

MusicXMLファイル(.musicxml / .xml / .mxl)を処理するときは、
**必ず以下の手順を守ること。XMLを直接読んで音符を解釈してはいけない。**

1. まず `parse_musicxml.py` を実行してJSONを生成する:
   ```bash
   python3 parse_musicxml.py 対象ファイル.musicxml
   ```
2. 生成されたJSONファイルを読み、そこに書かれた値だけを使う。
3. オクターブは必ずJSONの `octave` と `midi` の値を根拠にする。
   推測や目視でのXML読み取りは禁止。

## 理由

- LLMが生のXMLから音符を拾うとオクターブを読み違えることがある。
- music21によるパースは決定的で、移調楽器(アルトサックス等)の
  記譜音(written)と実音(sounding)も正確に分離される。

## JSONの読み方

- `written`  : 譜面に書かれている音(サックス奏者が見る音)
- `sounding` : 実際に鳴る音(ピアノ・コンサートピッチ)
- `midi`     : MIDIノート番号。オクターブの最終確認はこの値で行う
               (例: 中央ド C4 = 60)
- オクターブ表記はMusicXML標準(中央ド=C4)。
  ヤマハ式(中央ド=C3)とは1オクターブずれるので混同しないこと。

## music21が未インストールの場合

```bash
pip3 install music21
```

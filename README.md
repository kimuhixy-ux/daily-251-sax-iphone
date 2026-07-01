# Daily Ⅱ–Ⅴ–Ⅰ Sax Practice

iPhoneのSafariで使える、サックス向け251フレーズ練習PWAです。

## iPhoneでの使い方

1. このフォルダをGitHub Pages、Netlify、Vercelなどの静的ホスティングに置きます。
2. iPhoneのSafariで `index.html` のURLを開きます。
3. 共有ボタンを押します。
4. 「ホーム画面に追加」を選びます。
5. ホーム画面のアイコンから起動します。

一度開いたあとは、Service Workerのキャッシュによりオフラインでも再表示できます。

## ローカル確認

MacやPCで確認する場合、このフォルダに移動してローカルサーバーを起動します。

```bash
python3 -m http.server 8000
```

その後、ブラウザで以下を開きます。

```text
http://localhost:8000
```

## 内容

- Major 251 / Minor 251対応
- 12キー対応
- 毎日変わるフレーズ
- 今日のキーに戻すボタン
- 別フレーズを試すボタン
- オフラインキャッシュ対応

## ファイル構成

- `index.html`
- `manifest.webmanifest`
- `service-worker.js`
- `README.md`

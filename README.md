# ゆたぽんのおすすめ — 楽天ROOM 連携サイト

楽天ROOMに登録した商品を自動でウェブサイトに表示するシステムです。

## 仕組み

```
楽天ROOM を更新
    ↓
GitHub Actions が毎日自動実行（または手動実行）
    ↓
scrape_room.py が商品データを取得 → items.json を更新
    ↓
GitHub Pages がサイトを自動公開
    ↓
index.html が items.json を読み込んで商品を表示
```

## ファイル構成

| ファイル | 役割 |
|---|---|
| `index.html` | ウェブサイト本体 |
| `items.json` | 商品データ（自動生成） |
| `scrape_room.py` | 楽天ROOMスクレイピングスクリプト |
| `.github/workflows/update.yml` | GitHub Actions 自動更新ワークフロー |

## セットアップ

### 1. GitHubにリポジトリを作成してプッシュ

```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. GitHub Pages を有効化

1. リポジトリの **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **/ (root)**
4. **Save**

### 3. 自動更新の確認

- **Actions** タブで「楽天ROOM 自動更新」ワークフローが毎日 午前9時（JST）に実行されます
- 手動で実行する場合は **Actions** → **楽天ROOM 自動更新** → **Run workflow**

## 手動で商品データを更新する場合

```bash
pip install selenium requests beautifulsoup4
python scrape_room.py
```

## 楽天ROOMのURL

https://room.rakuten.co.jp/room_5a2045ed6a/items

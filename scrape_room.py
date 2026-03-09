#!/usr/bin/env python3
"""
楽天ROOMの商品データをスクレイピングして items.json を生成するスクリプト。
GitHub Actions で定期実行することで、楽天ROOMを更新すると自動でサイトも更新される。
"""

import json
import re
import time
import sys
from datetime import datetime, timezone, timedelta

ROOM_URL = "https://room.rakuten.co.jp/room_5a2045ed6a/items"
OUTPUT_FILE = "items.json"


def scrape_with_selenium():
    """Selenium でJavaScriptレンダリング後のデータを取得"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--lang=ja")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(ROOM_URL)

        # ページが読み込まれるまで待機
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='container--']"))
        )
        time.sleep(3)

        # スクロールして全商品を読み込む
        last_height = driver.execute_script("return document.body.scrollHeight")
        for _ in range(8):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # JavaScriptで商品データを取得
        items_data = driver.execute_script("""
            const containers = document.querySelectorAll('[class*="container--"]');
            const items = [];

            containers.forEach((c, i) => {
                const img = c.querySelector('img');
                const commentEl = c.querySelector('[class*="item-comment"]');

                if (!img || !commentEl) return;

                // 価格を探す
                const allEls = c.querySelectorAll('*');
                let priceText = null;
                let soldOut = false;
                allEls.forEach(el => {
                    if (el.children.length === 0) {
                        const text = el.textContent.trim();
                        if (text.includes('￥') || text.includes('¥')) {
                            priceText = text;
                        }
                        if (text === '売切れ') {
                            soldOut = true;
                        }
                    }
                });

                // コメント全文
                const comment = commentEl ? commentEl.innerText.trim() : '';

                // ハッシュタグを抽出
                const hashTagMatches = comment.match(/#[\\w\\u3040-\\u9FFF\\u30A0-\\u30FF\\uFF00-\\uFFEF]+/g) || [];

                // コメントからハッシュタグを除いた本文
                const commentBody = comment.replace(/#[\\w\\u3040-\\u9FFF\\u30A0-\\u30FF\\uFF00-\\uFFEF]+/g, '').trim();

                items.push({
                    index: i,
                    imgSrc: img.src,
                    price: priceText,
                    soldOut: soldOut,
                    likeCount: 0,
                    comment: commentBody,
                    hashTags: hashTagMatches.slice(0, 15)
                });
            });

            return items;
        """)

        return items_data

    finally:
        driver.quit()


def extract_title(comment):
    """コメントの最初の行をタイトルとして抽出"""
    if not comment:
        return "商品紹介"
    lines = [l.strip() for l in comment.split('\n') if l.strip()]
    if lines:
        title = lines[0]
        bracket_match = re.search(r'【([^】]+)】', title)
        if bracket_match:
            return f"【{bracket_match.group(1)}】"
        return title[:60] + ('…' if len(title) > 60 else '')
    return "商品紹介"


def main():
    print(f"楽天ROOM スクレイピング開始: {ROOM_URL}")

    items_data = []

    try:
        print("Selenium でスクレイピング中...")
        items_data = scrape_with_selenium()
        print(f"取得件数: {len(items_data)}")
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)

    # データを整形
    jst = timezone(timedelta(hours=9))
    output = {
        "updated_at": datetime.now(jst).strftime("%Y年%m月%d日 %H:%M"),
        "room_url": ROOM_URL,
        "items": []
    }

    for item in items_data:
        if not item.get("imgSrc"):
            continue

        img_src = item["imgSrc"]
        img_src_hd = re.sub(r'\?.*$', '', img_src)

        processed = {
            "index": item.get("index", 0),
            "imgSrc": img_src,
            "imgSrcHD": img_src_hd,
            "price": item.get("price", ""),
            "soldOut": item.get("soldOut", False),
            "likeCount": item.get("likeCount", 0),
            "comment": item.get("comment", ""),
            "hashTags": item.get("hashTags", []),
            "title": extract_title(item.get("comment", ""))
        }
        output["items"].append(processed)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"保存完了: {OUTPUT_FILE} ({len(output['items'])} 件)")


if __name__ == "__main__":
    main()

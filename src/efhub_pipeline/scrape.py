from _future_ import annotations

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


SITE_URL = "https://efhub.com/fr/players"
API_URL = "https://efhub.com/api/public/players"

SAVE_DIR = Path("data")
LATEST_JSON_FILE = SAVE_DIR / "efhub_LATEST.json"


def save_players(players_dict):
    """حفظ آمن وتدريجي للبيانات."""
    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = LATEST_JSON_FILE.with_suffix(".json.tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(players_dict, f, ensure_ascii=False, indent=2)

    os.replace(temp_file, LATEST_JSON_FILE)


async def scrape_players(max_pages=3):

    players_dict = {}
    failed_pages = []
    total_pages = None

    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)

        try:
            context = await browser.new_context(
                locale="en-GB",
                viewport={"width": 1365, "height": 900}
            )

            page = await context.new_page()

            print("🌐 فتح موقع eFHUB...")

            await page.goto(
                SITE_URL,
                wait_until="domcontentloaded",
                timeout=90000
            )

            await page.wait_for_timeout(3000)

            print("✅ تم فتح الموقع.")
            print("📡 بدء سحب بيانات API...")

            page_number = 1

            while True:

                if max_pages is not None and page_number > max_pages:
                    break

                params = {
                    "sort": "ReleaseDate",
                    "order": "desc",
                    "page": page_number
                }

                success = False

                for attempt in range(1, 4):

                    try:
                        result = await page.evaluate(
                            """async ({apiUrl, params}) => {
                                const url = new URL(apiUrl);

                                for (const [key, value] of Object.entries(params)) {
                                    url.searchParams.set(key, String(value));
                                }

                                const response = await fetch(url.toString(), {
                                    method: 'GET',
                                    credentials: 'include',
                                    headers: {'accept': '/'}
                                });

                                return {
                                    status: response.status,
                                    url: url.toString(),
                                    body: await response.text()
                                };
                            }""",
                            {
                                "apiUrl": API_URL,
                                "params": params
                            }
                        )

                        status = result["status"]

                        if status != 200:
                            print(
                                f"⚠️ الصفحة {page_number}: "
                                f"HTTP {status} — المحاولة {attempt}/3"
                            )
                            await page.wait_for_timeout(5000 * attempt)
                            continue

                        raw_data = json.loads(result["body"])

                        if not isinstance(raw_data, dict):
                            raise ValueError("استجابة API ليست JSON object.")

                        players_list = raw_data.get("players", [])

                        if not isinstance(players_list, list):
                            raise ValueError("قائمة اللاعبين غير صحيحة.")

                        if page_number == 1:
                            total_pages = raw_data.get("totalPages")
                            print(f"📚 عدد الصفحات حسب API: {total_pages}")

                        if not players_list:
                            print("🏁 الصفحة فارغة.")
                            success = True
                            page_number = None
                            break

                        added_count = 0

                        for player in players_list:

                            if not isinstance(player, dict):
                                continue

                            player_id = (
                                player.get("id")
                                or player.get("efhub_id")
                            )

                            if player_id is None:
                                continue

                            player_id = str(player_id)

                            players_dict[player_id] = player
                            added_count += 1

                        save_players(players_dict)

                        print(
                            f"✅ الصفحة {page_number}: "
                            f"{added_count} لاعب | "
                            f"الإجمالي الفريد: {len(players_dict)}"
                        )

                        success = True
                        break

                    except Exception as e:
                        print(
                            f"❌ خطأ في الصفحة {page_number} "
                            f"(المحاولة {attempt}/3): {e}"
                        )

                        await page.wait_for_timeout(5000 * attempt)

                if page_number is None:
                    break

                if not success:
                    failed_pages.append(page_number)
                    print("🛑 فشل تحميل الصفحة بعد 3 محاولات.")
                    break

                if (
                    total_pages is not None
                    and page_number >= int(total_pages)
                ):
                    print("🏁 تم الوصول إلى آخر صفحة.")
                    break

                page_number += 1
                await page.wait_for_timeout(1200)

        finally:
            await browser.close()

    save_players(players_dict)

    print("\n" + "=" * 45)
    print("📊 تقرير السحب")
    print("=" * 45)
    print(f"👥 إجمالي اللاعبين الفريدين: {len(players_dict)}")
    print(f"⚠️ الصفحات التي فشل سحبها: {failed_pages}")
    print(f"📁 ملف الحفظ: {LATEST_JSON_FILE}")
    print("=" * 45)

    if failed_pages:
        raise RuntimeError(f"فشل سحب الصفحات: {failed_pages}")

    if not players_dict:
        raise RuntimeError("لم يتم جمع أي لاعب.")

    return players_dict


async def main():
    await scrape_players(max_pages=3)


if _name_ == "_main_":
    asyncio.run(main())

import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


DATA_DIR = Path("data")

INPUT_FILE = DATA_DIR / "new_players_ready.json"
OUTPUT_FILE = DATA_DIR / "new_players_detailed.json"

SITE_URL = "https://efhub.com/fr/players"
PLAYER_API = "https://efhub.com/api/public/players"

CHUNK_SIZE = 15


def save_detailed(data):
    """حفظ آمن وتدريجي للتفاصيل."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = OUTPUT_FILE.with_suffix(".json.tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp_file, OUTPUT_FILE)


async def fetch_player_details(max_retries=3):

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"لم يتم العثور على ملف اللاعبين الجدد: {INPUT_FILE}"
        )

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        new_players = json.load(f)

    if not isinstance(new_players, dict):
        raise ValueError("ملف اللاعبين الجدد ليس JSON object.")

    if not new_players:
        print("⚠️ لا يوجد لاعبون جدد لجلب تفاصيلهم.")
        save_detailed({})
        return {}

    # استئناف العمل من البيانات المحفوظة سابقًا
    detailed = {}

    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                previous = json.load(f)

            if isinstance(previous, dict):
                detailed = previous

        except (json.JSONDecodeError, OSError):
            print("⚠️ تعذر قراءة ملف التفاصيل السابق، سنبدأ من جديد.")

    remaining = [
        str(pid)
        for pid in new_players
        if str(pid) not in detailed
    ]

    print(
        f"🎯 إجمالي اللاعبين: {len(new_players)} "
        f"| المتبقي: {len(remaining)}"
    )

    if not remaining:
        print("🎉 تم جلب تفاصيل جميع اللاعبين بالفعل.")
        return detailed

    ok = 0
    fail = 0

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

            total = len(remaining)

            for i in range(0, total, CHUNK_SIZE):

                chunk = remaining[i:i + CHUNK_SIZE]
                result = None

                for attempt in range(1, max_retries + 1):

                    try:
                        result = await page.evaluate(
                            """async ({baseUrl, pids}) => {
                                const out = {};

                                for (const pid of pids) {
                                    try {
                                        const response = await fetch(
                                            ${baseUrl}/${encodeURIComponent(pid)},
                                            {
                                                method: 'GET',
                                                credentials: 'include',
                                                headers: {
                                                    'accept': '/'
                                                }
                                            }
                                        );

                                        if (response.ok) {
                                            out[pid] = await response.json();
                                        } else {
                                            out[pid] = {
                                                _status_: response.status
                                            };
                                        }

                                    } catch (error) {
                                        out[pid] = {
                                            _error_: String(error)
                                        };
                                    }

                                    await new Promise(resolve =>
                                        setTimeout(
                                            resolve,
                                            400 + Math.random() * 400
                                        )
                                    );
                                }

                                return out;
                            }""",
                            {
                                "baseUrl": PLAYER_API,
                                "pids": chunk
                            }
                        )

                        break

                    except Exception as e:
                        print(
                            f"⚠️ فشل الدفعة "
                            f"({attempt}/{max_retries}): {e}"
                        )

                        await page.wait_for_timeout(5000 * attempt)

                if not isinstance(result, dict):
                    fail += len(chunk)
                    continue

                for pid in chunk:

                    player_data = result.get(pid)

                    if (
                        isinstance(player_data, dict)
                        and "_status_" not in player_data
                        and "_error_" not in player_data
                        and "error" not in player_data
                    ):
                        detailed[pid] = player_data
                        ok += 1

                    else:
                        print(
                            f"⚠️ فشل جلب تفاصيل اللاعب {pid}: "
                            f"{player_data}"
                        )
                        fail += 1

                save_detailed(detailed)

                done = min(i + CHUNK_SIZE, total)

                print(
                    f"✅ [{done}/{total}] "
                    f"نجاح: {ok} | فشل: {fail}"
                )

                await page.wait_for_timeout(1000)

        finally:
            await browser.close()

    save_detailed(detailed)

    print("\n" + "=" * 50)
    print("📊 تقرير التفاصيل")
    print("=" * 50)
    print(f"👥 إجمالي اللاعبين الجدد: {len(new_players)}")
    print(f"✅ نجاح: {ok}")
    print(f"❌ فشل: {fail}")
    print(f"📁 ملف التفاصيل: {OUTPUT_FILE}")
    print("=" * 50)

    if fail:
        raise RuntimeError(
            f"فشل جلب تفاصيل {fail} لاعب. "
            "البيانات الناجحة محفوظة ويمكن استكمال العمل لاحقًا."
        )

    return detailed


async def main():
    await fetch_player_details()


if _name_ == "_main_":
    asyncio.run(main())

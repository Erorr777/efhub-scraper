import json
import os
from pathlib import Path

from supabase import create_client

from .config import Settings


DATA_DIR = Path("data")
LATEST_FILE = DATA_DIR / "efhub_LATEST.json"
NEW_PLAYERS_FILE = DATA_DIR / "new_players_ready.json"


def save_json(data, file_path):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    temp_file = file_path.with_suffix(file_path.suffix + ".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    os.replace(temp_file, file_path)


def fetch_all_existing_ids(supabase):
    existing = set()
    limit = 1000
    offset = 0

    while True:
        response = (
            supabase.table("players")
            .select("efhub_id")
            .range(offset, offset + limit - 1)
            .execute()
        )

        rows = response.data or []

        if not rows:
            break

        for row in rows:
            player_id = row.get("efhub_id")

            if player_id is not None:
                existing.add(str(player_id))

        print(
            f"📥 Supabase: تم فحص {len(existing)} ID"
        )

        if len(rows) < limit:
            break

        offset += limit

    return existing


def find_new_players(settings: Settings):

    if not LATEST_FILE.exists():
        raise FileNotFoundError(
            f"لم يتم العثور على ملف اللاعبين: {LATEST_FILE}"
        )

    with open(LATEST_FILE, "r", encoding="utf-8") as f:
        latest_data = json.load(f)

    if not isinstance(latest_data, dict):
        raise ValueError("ملف اللاعبين ليس JSON object.")

    print("🔌 الاتصال بـ Supabase...")

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

    print("📥 جاري فحص قاعدة البيانات...")

    existing_ids = fetch_all_existing_ids(supabase)

    new_players = {
        str(pid): player
        for pid, player in latest_data.items()
        if (
            isinstance(player, dict)
            and "error" not in player
            and str(pid) not in existing_ids
        )
    }

    print("=" * 50)
    print(f"👥 الملف: {len(latest_data)}")
    print(f"💾 Supabase: {len(existing_ids)}")
    print(f"🚨 جديد: {len(new_players)}")
    print("=" * 50)

    for pid, player in list(new_players.items())[:7]:
        print(
            f"➖ {player.get('name', '?')} "
            f"(OVR {player.get('overallRating', '-')}) "
            f"- ID {pid}"
        )

    save_json(new_players, NEW_PLAYERS_FILE)

    print(f"✅ تم حفظ {len(new_players)} لاعب جديد.")
    print(f"📁 الملف: {NEW_PLAYERS_FILE}")

    return new_players

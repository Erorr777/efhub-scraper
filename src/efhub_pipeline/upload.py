import json
from datetime import datetime
from pathlib import Path

from supabase import create_client

from .config import Settings


DATA_DIR = Path("data")
DETAILED_FILE = DATA_DIR / "new_players_detailed.json"

PLAYER_TYPE_MAP = {
    1: "Standard",
    2: "Trending",
    3: "Highlight",
    4: "Legendary",
    5: "Epic",
    6: "ShowTime",
    7: "BigTime",
}

BATCH_SIZE = 200


def fetch_valid_ids(supabase, table):
    """تحميل IDs المرجعية من جداول Supabase."""
    ids = set()
    limit = 1000
    offset = 0

    while True:
        response = (
            supabase.table(table)
            .select("id")
            .range(offset, offset + limit - 1)
            .execute()
        )

        rows = response.data or []

        if not rows:
            break

        for row in rows:
            if row.get("id") is not None:
                ids.add(row["id"])

        if len(rows) < limit:
            break

        offset += limit

    print(f"📥 {table}: تم تحميل {len(ids)} ID")
    return ids


def is_valid_player(player):
    return (
        isinstance(player, dict)
        and "_status_" not in player
        and "_error_" not in player
        and "error" not in player
    )


def to_int(value, default=0):
        try:
            return int(value) if value is not None else default
        except (ValueError, TypeError):
            return default

    player_type = to_int(player.get("playerType"), 1)

    card_type = PLAYER_TYPE_MAP.get(
        player_type,
        f"Type_{player_type}"
    )

    boost_id = to_int(player.get("boostId"), 0)
    has_booster = boost_id > 0

    base_ovr = to_int(
        player.get("overallRating") or player.get("ovr"),
        0
    )

    max_ovr = to_int(
        player.get("maxOverallRating") or player.get("maxOvr"),
        base_ovr
    )

    level_cap = to_int(
        player.get("levelCap") or player.get("maxLevel"),
        1
    )

    progression_points = max(0, (level_cap - 1) * 2)

    row = {
        "efhub_id": str(pid),
        "name": player.get("name", "Unknown"),
        "card_booster": "true" if has_booster else "false",
        "booster_one": (
            boost_id if boost_id in valid_boosters else None
        ),
        "booster_two": None,
        "base_ovr": base_ovr,
        "max_ovr": max_ovr,
        "position": player.get("position"),
        "playstyle": player.get("playingStyle") or "None",
        "foot": player.get("preferredFoot"),
        "set_piece": stats.get("setPieceTaking"),
        "tackling": stats.get("ballWinning"),
        "gk_parrying": stats.get("gkClearing"),
        "jumping_height_physics": model.get("jumpingHeight"),
        "release_date": now,
        "national_name": player.get("nationality"),
        "club_name": player.get("team"),
        "age": player.get("age"),
        "height": player.get("height"),
        "weight": player.get("weight"),
        "condition": player.get("condition"),
        "form": player.get("form"),
        "injury_resistance": player.get("injuryResistance"),
        "offensive_awareness": stats.get("offensiveAwareness"),
        "ball_control": stats.get("ballControl"),
        "dribbling": stats.get("dribbling"),
        "tight_possession": stats.get("tightPossession"),
        "low_pass": stats.get("lowPass"),
        "lofted_pass": stats.get("loftedPass"),
        "finishing": stats.get("finishing"),
        "heading": stats.get("heading"),
        "curl": stats.get("curl"),
        "speed": stats.get("speed"),
        "acceleration": stats.get("acceleration"),
        "kicking_power": stats.get("kickingPower"),
        "jump": stats.get("jump"),
        "physical_contact": stats.get("physicalContact"),
        "balance": stats.get("balance"),
        "stamina": stats.get("stamina"),
        "defensive_awareness": stats.get("defensiveAwareness"),
        "aggression": stats.get("aggression"),
        "defensive_engagement": stats.get("trackingBack"),
        "gk_awareness": stats.get("gkAwareness"),
        "gk_catching": stats.get("gkCatching"),
        "gk_reflexes": stats.get("gkReflexes"),
        "gk_reach": stats.get("gkReach"),
        "arm_length": model.get("armLength"),
        "shoulder_width": model.get("shoulderWidth"),
        "neck_length": model.get("neckLength"),
        "chest_measurement": model.get("chestMeasurement"),
        "neck_size": model.get("neckSize"),
        "shoulder_height": model.get("shoulderHeight"),
        "leg_length": model.get("legLength"),
        "thigh_size": model.get("thighSize"),
        "waist_size": model.get("waistSize"),
        "arm_size": model.get("armSize"),
        "calf_size": model.get("calfSize"),
        "leg_coverage_radius": model.get("legCoverageRadius"),
        "arm_coverage_radius": model.get("armCoverageRadius"),
        "torso_collision": model.get("torsoCollision"),
        "leg_length_based_height": (
            model.get("legLengthBasedHeight")
            or model.get("legLength")
        ),
        "weak_foot_usage": player.get("weakFootUsage"),
        "weak_foot_accuracy": player.get("weakFootAccuracy"),
        "nation_id": (
            player.get("countryId")
            if player.get("countryId") in valid_nations
            else None
        ),
        "club_id": (
            player.get("teamId")
            if player.get("teamId") in valid_clubs
            else None
        ),
        "league_id": (
            player.get("leagueId")
            if player.get("leagueId") in valid_leagues
            else None
        ),
        "card_type": card_type,
        "price_gp": player.get("price"),
        "level_cap": level_cap,
        "max_level": level_cap,
        "progression_points": progression_points,
        "total_progression_points": progression_points,
        "skills": player.get("skills", []),
        "com_skills": player.get("comSkills", []),
        "positions_ratings": player.get("additionalPositions", []),
    }

    return {
        key: value
        for key, value in row.items()
        if value is not None
    }


def upload_players(settings: Settings):

    if not DETAILED_FILE.exists():
        raise FileNotFoundError(
            f"لم يتم العثور على ملف التفاصيل: {DETAILED_FILE}"
        )

    with open(DETAILED_FILE, "r", encoding="utf-8") as f:
        detailed = json.load(f)

    if not isinstance(detailed, dict):
        raise ValueError("ملف التفاصيل ليس JSON object.")

    valid_players = {
        str(pid): player
        for pid, player in detailed.items()
        if is_valid_player(player)
    }

    if not valid_players:
        print("⚠️ لا توجد بيانات صالحة للرفع.")
        return 0

    print("🔌 الاتصال بـ Supabase...")

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )

    print("📥 تحميل IDs المرجعية...")

    valid_clubs = fetch_valid_ids(supabase, "clubs")
    valid_leagues = fetch_valid_ids(supabase, "leagues")
    valid_nations = fetch_valid_ids(supabase, "countries")
    valid_boosters = fetch_valid_ids(supabase, "boosters")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = []

    for pid, player in valid_players.items():
        try:
            row = build_player_row(
                pid,
                player,
                valid_clubs,
                valid_leagues,
                valid_nations,
                valid_boosters,
                now,
            )
            payload.append(row)

        except Exception as e:
            raise RuntimeError(
                f"فشل تجهيز بيانات اللاعب {pid}: {e}"
            ) from e

    if not payload:
        print("⚠️ لا توجد بيانات جاهزة للرفع.")
        return 0

    print(f"📡 تجهيز رفع {len(payload)} لاعب...")

    uploaded = 0

    for i in range(0, len(payload), BATCH_SIZE):
        batch = payload[i:i + BATCH_SIZE]

        try:
            (
                supabase.table("players")
                .upsert(batch, on_conflict="efhub_id")
                .execute()
            )

            uploaded += len(batch)

            print(
                f"✔️ تم رفع {uploaded}/{len(payload)} لاعب"
            )

        except Exception as e:
            raise RuntimeError(
                f"فشل رفع الدفعة التي تبدأ عند اللاعب رقم {i}: {e}"
            ) from e

    print("\n" + "=" * 50)
    print(f"🎉 اكتمل رفع {uploaded} لاعب.")
    print("=" * 50)

    return uploaded

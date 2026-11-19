import asyncio

from .config import Settings
from .scrape import scrape_players


def run_pipeline(settings: Settings) -> None:
    print("=" * 50)
    print("eFHUB PIPELINE")
    print("=" * 50)

    max_pages = settings.max_pages if settings.max_pages > 0 else None

    print(f"MAX_PAGES: {max_pages or 'ALL'}")
    print("STEP 1: Scraping players")

    players = asyncio.run(
        scrape_players(max_pages=max_pages)
    )

    print(f"STEP 1 COMPLETE: {len(players)} players collected")

    print("=" * 50)
    print("STEP 1 SUCCESS")
    print("Remaining stages are not connected yet.")
    print("=" * 50)

    raise RuntimeError(
        "Pipeline is intentionally stopped after Step 1. "
        "Supabase, player details, and image processing are not connected yet."
    )

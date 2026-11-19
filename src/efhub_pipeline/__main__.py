from .config import load_settings
from .pipeline import run_pipeline

def main() -> None:
    settings = load_settings()
    print(f"Starting eFHUB pipeline (MAX_PAGES={settings.max_pages}, RUN_IMAGES={settings.run_images})")
    run_pipeline(settings)

if __name__ == "__main__":
    main()

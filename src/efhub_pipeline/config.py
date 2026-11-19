import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    r2_account_id: str
    r2_access_key_id: str
    r2_secret_access_key: str
    r2_bucket_name: str
    r2_public_url: str
    max_pages: int
    run_images: bool

def load_settings() -> Settings:
    required = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
        "R2_ACCOUNT_ID": os.getenv("R2_ACCOUNT_ID"),
        "R2_ACCESS_KEY_ID": os.getenv("R2_ACCESS_KEY_ID"),
        "R2_SECRET_ACCESS_KEY": os.getenv("R2_SECRET_ACCESS_KEY"),
        "R2_BUCKET_NAME": os.getenv("R2_BUCKET_NAME"),
        "R2_PUBLIC_URL": os.getenv("R2_PUBLIC_URL"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing GitHub Secrets: " + ", ".join(missing))

    raw_pages = os.getenv("MAX_PAGES", "3")
    max_pages = int(raw_pages)
    if max_pages < 0:
        raise ValueError("MAX_PAGES must be 0 or a positive integer")

    return Settings(
        supabase_url=required["SUPABASE_URL"],
        supabase_service_role_key=required["SUPABASE_SERVICE_ROLE_KEY"],
        r2_account_id=required["R2_ACCOUNT_ID"],
        r2_access_key_id=required["R2_ACCESS_KEY_ID"],
        r2_secret_access_key=required["R2_SECRET_ACCESS_KEY"],
        r2_bucket_name=required["R2_BUCKET_NAME"],
        r2_public_url=required["R2_PUBLIC_URL"],
        max_pages=max_pages,
        run_images=os.getenv("RUN_IMAGES", "false").lower() == "true",
    )

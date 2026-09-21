import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True, slots=True)
class Config:
    token: str
    admin_id: int
    db_path: str


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id = os.getenv("ADMIN_ID", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN не задан (см. .env.example)")
    if not admin_id.isdigit():
        raise SystemExit("ADMIN_ID не задан или не является числом (см. .env.example)")
    return Config(
        token=token,
        admin_id=int(admin_id),
        db_path=os.getenv("DB_PATH", "silxnce.db"),
    )

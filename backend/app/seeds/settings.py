import json

from sqlalchemy.orm import Session

from app.models.settings import AppSetting

DEFAULT_SETTINGS = [
    ("app.language", "es"),
    ("theme.mode", "dark"),
    ("app.currency", "EUR"),
]


def seed_settings(db: Session) -> None:
    for key, value in DEFAULT_SETTINGS:
        if not db.query(AppSetting).filter(AppSetting.key == key).first():
            db.add(AppSetting(key=key, value_json=json.dumps(value)))
    db.commit()

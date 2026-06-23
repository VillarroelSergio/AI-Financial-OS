from sqlalchemy.orm import Session

from app.models.category import Category

SYSTEM_CATEGORIES = [
    {"name": "Alimentación", "type": "expense", "icon": "shopping-cart", "color": "#00a87e"},
    {"name": "Restaurante", "type": "expense", "icon": "utensils", "color": "#494fdf"},
    {"name": "Casa", "type": "expense", "icon": "home", "color": "#ec7e00"},
    {"name": "Transporte", "type": "expense", "icon": "car", "color": "#8d969e"},
    {"name": "Ocio", "type": "expense", "icon": "gamepad-2", "color": "#b09000"},
    {"name": "Comunicaciones", "type": "expense", "icon": "smartphone", "color": "#505a63"},
    {"name": "Salud", "type": "expense", "icon": "heart-pulse", "color": "#e23b4a"},
    {"name": "Mascotas", "type": "expense", "icon": "paw-print", "color": "#00a87e"},
    {"name": "Regalos", "type": "expense", "icon": "gift", "color": "#4f55f1"},
    {"name": "Ropa", "type": "expense", "icon": "shirt", "color": "#b09000"},
    {"name": "Deportes", "type": "expense", "icon": "dumbbell", "color": "#494fdf"},
    {"name": "Salario", "type": "income", "icon": "briefcase", "color": "#00a87e"},
    {"name": "Ahorros", "type": "income", "icon": "piggy-bank", "color": "#494fdf"},
    {"name": "Depósitos", "type": "investment", "icon": "landmark", "color": "#ec7e00"},
    {"name": "Otros", "type": "expense", "icon": "circle-ellipsis", "color": "#505a63"},
]


def seed_categories(db: Session) -> None:
    if db.query(Category).count() > 0:
        return
    for data in SYSTEM_CATEGORIES:
        db.add(Category(**data, is_system=True))
    db.commit()

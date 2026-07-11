"""Categorización automática de movimientos importados sin categoría.

Cuando el archivo no trae columna de categoría (Revolut, BBVA, genéricos), se
asigna una por palabras clave del comercio. Los nombres son las categorías de
sistema de seeds/categories.py, así el import las reutiliza sin crear nuevas.

Reglas de coincidencia: las claves con espacio casan por subcadena; las de una
sola palabra casan por prefijo de token ("cine" → "Cinesur", pero "bar" NO casa
con "Barajas" porque los términos genéricos van al final, tras "aeropuerto").
La primera coincidencia por orden de inserción gana.
"""

import unicodedata

KEYWORD_CATEGORIES: dict[str, str] = {
    # Comida a domicilio antes que transporte ("uber eats" vs "uber").
    "uber eats": "Restaurante",
    "glovo": "Restaurante",
    "just eat": "Restaurante",
    # Alimentación
    "mercadona": "Alimentación",
    "dia": "Alimentación",
    "aldi": "Alimentación",
    "lidl": "Alimentación",
    "supercor": "Alimentación",
    "alcampo": "Alimentación",
    "carrefour": "Alimentación",
    "gadis": "Alimentación",
    "suma": "Alimentación",
    "supermercado": "Alimentación",
    "super market": "Alimentación",
    "fruteria": "Alimentación",
    "frutas": "Alimentación",
    "carniceria": "Alimentación",
    "alimentacion": "Alimentación",
    "panaderia": "Alimentación",
    "benipan": "Alimentación",
    "horno": "Alimentación",
    "boutique del pan": "Alimentación",
    # Suscripciones y tecnología
    "apple": "Comunicaciones",
    "microsoft": "Comunicaciones",
    "disney": "Comunicaciones",
    "netflix": "Comunicaciones",
    "spotify": "Comunicaciones",
    "hbo": "Comunicaciones",
    "amazon prime": "Comunicaciones",
    "openai": "Comunicaciones",
    "chatgpt": "Comunicaciones",
    "claude": "Comunicaciones",
    "kaspersky": "Comunicaciones",
    "movistar": "Comunicaciones",
    "vodafone": "Comunicaciones",
    "orange": "Comunicaciones",
    "digi": "Comunicaciones",
    "telefonica": "Comunicaciones",
    "el pais": "Comunicaciones",
    "elordenmundial": "Comunicaciones",
    # Juegos, ocio y viajes
    "estanco": "Ocio",
    "tabaco": "Ocio",
    "vape": "Ocio",
    "steam": "Ocio",
    "battle.net": "Ocio",
    "blizzard": "Ocio",
    "playstation": "Ocio",
    "nintendo": "Ocio",
    "instant gaming": "Ocio",
    "riot games": "Ocio",
    "xsolla": "Ocio",
    "eurosport": "Ocio",
    "filmin": "Ocio",
    "cine": "Ocio",
    "film": "Ocio",
    "entradas": "Ocio",
    "resident advisor": "Ocio",
    "museo": "Ocio",
    "fever": "Ocio",
    "woutick": "Ocio",
    "giglon": "Ocio",
    "bowling": "Ocio",
    "disco": "Ocio",
    "hangar": "Ocio",
    "festival": "Ocio",
    "canoas": "Ocio",
    "hotel": "Ocio",
    "airbnb": "Ocio",
    "booking": "Ocio",
    "cartrawler": "Ocio",
    # Transporte (antes que restauración: "Parking Aeropuerto ... Barajas")
    "renfe": "Transporte",
    "alsa": "Transporte",
    "metro": "Transporte",
    "emt": "Transporte",
    "consorcio regional de transportes": "Transporte",
    "bolt": "Transporte",
    "cabify": "Transporte",
    "uber": "Transporte",
    "taxi": "Transporte",
    "lic ": "Transporte",
    "licencia": "Transporte",
    "telpark": "Transporte",
    "parking": "Transporte",
    "indigo": "Transporte",
    "garaje": "Transporte",
    "autopista": "Transporte",
    "cepsa": "Transporte",
    "repsol": "Transporte",
    "plenergy": "Transporte",
    "gasolinera": "Transporte",
    "e.s ": "Transporte",
    "aena": "Transporte",
    "aeropuerto": "Transporte",
    # Salud
    "farmacia": "Salud",
    "dental": "Salud",
    "fisio": "Salud",
    "psico": "Salud",
    "optica": "Salud",
    "asisa": "Salud",
    "sanitas": "Salud",
    "adeslas": "Salud",
    # Mascotas (antes que Salud genérica por "clinica veterinaria")
    "veterinari": "Mascotas",
    "guaw": "Mascotas",
    "kiwoko": "Mascotas",
    # Ropa
    "zara": "Ropa",
    "bershka": "Ropa",
    "pull&bear": "Ropa",
    "pull and bear": "Ropa",
    "zalando": "Ropa",
    "asos": "Ropa",
    "calzedonia": "Ropa",
    "primark": "Ropa",
    "meller": "Ropa",
    "shein": "Ropa",
    # Deporte
    "decathlon": "Deportes",
    "fitness": "Deportes",
    "gym": "Deportes",
    "synergym": "Deportes",
    "padel": "Deportes",
    "myprotein": "Deportes",
    "asics": "Deportes",
    "saucony": "Deportes",
    "new balance": "Deportes",
    "runrun": "Deportes",
    # Casa
    "leroy merlin": "Casa",
    "ikea": "Casa",
    "iberdrola": "Casa",
    "endesa": "Casa",
    "naturgy": "Casa",
    "facsa": "Casa",
    "tagus": "Casa",
    "aqualia": "Casa",
    "canal de isabel": "Casa",
    "alquiler": "Casa",
    "bricodepot": "Casa",
    "espacio casa": "Casa",
    "pepco": "Casa",
    "milbby": "Casa",
    # Restauración (términos genéricos al final para no pisar lo anterior)
    "bar": "Restaurante",
    "burger": "Restaurante",
    "mcdonald": "Restaurante",
    "kebab": "Restaurante",
    "restaurant": "Restaurante",
    "cafeteria": "Restaurante",
    "cafe": "Restaurante",
    "taberna": "Restaurante",
    "pizz": "Restaurante",
    "sushi": "Restaurante",
    "ramen": "Restaurante",
    "terraza": "Restaurante",
    "heladeria": "Restaurante",
    "churr": "Restaurante",
    "chocolate": "Restaurante",
    "vicio": "Restaurante",
    "arroceria": "Restaurante",
    "asador": "Restaurante",
    "tapas": "Restaurante",
    "vinos": "Restaurante",
    "hosteleria": "Restaurante",
    # Ingresos
    "nomina": "Salario",
    "salario": "Salario",
}


# Palabras genéricas cortas que solo casan como token exacto: por prefijo
# producen falsos positivos ("dia" → "diagnóstico", "bar" → "Barbería").
EXACT_TOKEN_KEYWORDS = {"dia", "suma", "bar", "cafe", "film", "disco", "metro", "emt"}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in text if not unicodedata.combining(c))


def learned_category(db, description: str) -> str | None:
    """Nombre de categoría aprendida de correcciones manuales, o None."""
    from app.models.category import Category
    from app.models.merchant_rule import MerchantRule

    rule = db.query(MerchantRule).filter(MerchantRule.merchant == _normalize(description)).first()
    if rule is None:
        return None
    category = db.query(Category).filter(Category.id == rule.category_id).first()
    return category.name if category else None


def auto_category(description: str) -> str | None:
    """Devuelve el nombre de categoría de sistema para un comercio, o None."""
    normalized = _normalize(description)
    tokens = normalized.split()
    for keyword, category in KEYWORD_CATEGORIES.items():
        if " " in keyword or "." in keyword:
            if keyword in normalized:
                return category
        elif keyword in EXACT_TOKEN_KEYWORDS:
            if keyword in tokens:
                return category
        elif any(token.startswith(keyword) for token in tokens):
            return category
    return None

"""Clasificación heurística de recibos domésticos en importaciones.

Dos niveles: marcas conocidas (siempre clasifican) y palabras genéricas de
servicio, que solo clasifican si el concepto además parece un recibo
("adeudo", "recibo", "factura"). Así "Peluquería Luz" no se convierte en
factura de electricidad pero "Adeudo recibo luz" sí.
"""

SERVICE_LABELS = {
    "electricity": "Luz",
    "gas": "Gas",
    "water": "Agua",
    "internet": "Internet",
    "phone": "Telefonía",
    "home_insurance": "Seguro hogar",
    "rent_mortgage": "Alquiler / hipoteca",
    "community": "Comunidad",
}

# ponytail: lista fija de marcas españolas habituales; ampliar aquí cuando aparezca un proveedor nuevo.
_BRANDS: list[tuple[str, str, str]] = [
    ("iberdrola", "electricity", "Iberdrola"),
    ("endesa", "electricity", "Endesa"),
    ("holaluz", "electricity", "Holaluz"),
    ("octopus energy", "electricity", "Octopus Energy"),
    ("naturgy", "gas", "Naturgy"),
    ("gas natural", "gas", "Gas Natural"),
    ("aqualia", "water", "Aqualia"),
    ("canal de isabel", "water", "Canal de Isabel II"),
    ("emasesa", "water", "Emasesa"),
    ("movistar", "internet", "Movistar"),
    ("vodafone", "internet", "Vodafone"),
    ("orange", "internet", "Orange"),
    ("masmovil", "internet", "MásMóvil"),
    ("pepephone", "internet", "Pepephone"),
    ("digi spain", "internet", "Digi"),
    ("lowi", "internet", "Lowi"),
    ("jazztel", "internet", "Jazztel"),
    ("mapfre", "home_insurance", "Mapfre"),
    ("linea directa", "home_insurance", "Línea Directa"),
    ("línea directa", "home_insurance", "Línea Directa"),
    ("mutua madrile", "home_insurance", "Mutua Madrileña"),
]

_GENERIC: list[tuple[str, str]] = [
    ("electricidad", "electricity"),
    ("luz", "electricity"),
    ("gas", "gas"),
    ("agua", "water"),
    ("internet", "internet"),
    ("fibra", "internet"),
    ("telefonia", "phone"),
    ("telefonía", "phone"),
    ("seguro", "home_insurance"),
    ("alquiler", "rent_mortgage"),
    ("hipoteca", "rent_mortgage"),
    ("comunidad de propietarios", "community"),
    ("cdad. prop", "community"),
]

_BILL_HINTS = ("adeudo", "recibo", "factura")


def classify_bill(description: str) -> tuple[str, str] | None:
    """Devuelve (service_type, proveedor) si el concepto parece un recibo doméstico."""
    d = description.casefold()
    for keyword, service, provider in _BRANDS:
        if keyword in d:
            return service, provider
    if any(hint in d for hint in _BILL_HINTS):
        for keyword, service in _GENERIC:
            if keyword in d:
                return service, description.strip()[:40] or SERVICE_LABELS[service]
    return None


if __name__ == "__main__":
    assert classify_bill("ADEUDO RECIBO IBERDROLA CLIENTES") == ("electricity", "Iberdrola")
    assert classify_bill("Recibo luz vivienda") == ("electricity", "Recibo luz vivienda")
    assert classify_bill("Peluqueria Luz") is None
    assert classify_bill("Mercadona") is None
    assert classify_bill("Factura alquiler julio")[0] == "rent_mortgage"
    print("bill_classifier OK")

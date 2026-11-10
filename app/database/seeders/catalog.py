from sqlalchemy.orm import Session
from app.models.allergen_model import Allergen

EU_ALLERGENS = [
    {"code": "GLUTEN", "name": "Cereales que contienen gluten"},
    {"code": "CRUSTACEOS", "name": "Crustáceos y productos a base de crustáceos"},
    {"code": "HUEVOS", "name": "Huevos y productos a base de huevo"},
    {"code": "PESCADO", "name": "Pescado y productos a base de pescado"},
    {"code": "CACAHUETES", "name": "Cacahuetes y productos a base de cacahuetes"},
    {"code": "SOJA", "name": "Soja y productos a base de soja"},
    {"code": "LACTEOS", "name": "Leche y sus derivados (incluida la lactosa)"},
    {"code": "FRUTOS_DE_CASCARA", "name": "Frutos de cáscara"},
    {"code": "APIO", "name": "Apio y productos derivados"},
    {"code": "MOSTAZA", "name": "Mostaza y productos derivados"},
    {"code": "SESAMO", "name": "Granos de sésamo y productos derivados"},
    {"code": "SULFITOS", "name": "Dióxido de azufre y sulfitos"},
    {"code": "ALTRAMUCES", "name": "Altramuces y productos a base de altramuces"},
    {"code": "MOLUSCOS", "name": "Moluscos y productos a base de moluscos"},
]


def seed_allergens(db: Session) -> list[Allergen]:
    seeded = []
    for item in EU_ALLERGENS:
        existing = db.query(Allergen).filter(Allergen.code == item["code"]).first()
        if existing is None:
            new_allergen = Allergen(code=item["code"], name=item["name"])
            db.add(new_allergen)
            seeded.append(new_allergen)
        else:
            seeded.append(existing)

    db.commit()
    return seeded

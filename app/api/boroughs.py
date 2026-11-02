from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.api.deps import get_db
from app.db.models import Borough

router = APIRouter(prefix="/boroughs", tags=["boroughs"])


@router.get("")
def list_boroughs(db: Session = Depends(get_db)):
    boroughs = db.query(Borough).order_by(Borough.name).all()
    return [{"id": b.id, "name": b.name, "population": b.population} for b in boroughs]


@router.get("/{name}")
def get_borough(name: str, db: Session = Depends(get_db)):
    borough = db.query(Borough).filter(Borough.name.ilike(name)).first()
    if borough is None:
        raise HTTPException(status_code=404, detail=f"Borough '{name}' not found")

    shape = to_shape(borough.geom)
    return {
        "id": borough.id,
        "name": borough.name,
        "population": borough.population,
        "geometry": shape.__geo_interface__,
    }

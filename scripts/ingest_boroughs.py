"""One-off script to load London borough boundaries into the database."""

import geopandas as gpd
from geoalchemy2.shape import from_shape

from app.db.session import SessionLocal
from app.db.models import Borough

SHAPEFILE_PATH = "data/raw/london_boundaries/ESRI/London_Borough_Excluding_MHW.shp"
TARGET_CRS = "EPSG:4326"


def main():
    print(f"Reading shapefile from {SHAPEFILE_PATH} ...")
    gdf = gpd.read_file(SHAPEFILE_PATH)

    print(f"Reprojecting from {gdf.crs} to {TARGET_CRS} ...")
    gdf = gdf.to_crs(TARGET_CRS)

    db = SessionLocal()
    try:
        inserted = 0
        for _, row in gdf.iterrows():
            geom = row.geometry
            # PostGIS column is MULTIPOLYGON, but some rows might be plain
            # POLYGON after reprojection/reading — normalize them.
            if geom.geom_type == "Polygon":
                from shapely.geometry import MultiPolygon

                geom = MultiPolygon([geom])

            borough = Borough(
                name=row["NAME"],
                population=None,
                geom=from_shape(geom, srid=4326),
            )
            db.add(borough)
            inserted += 1

        db.commit()
        print(f"Inserted {inserted} boroughs.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

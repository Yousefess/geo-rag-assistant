"""One-off script to add population data to existing boroughs."""

import pandas as pd

from app.db.session import SessionLocal
from app.db.models import Borough

CSV_PATH = "data/raw/borough_population.csv"
TARGET_YEAR = 2010
TARGET_SOURCE = "ONS MYE"


def main():
    print(f"Reading population data from {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH)

    filtered = df[(df["Year"] == TARGET_YEAR) & (df["Source"] == TARGET_SOURCE)]
    print(f"Found {len(filtered)} rows for year={TARGET_YEAR}, source={TARGET_SOURCE}")

    db = SessionLocal()
    try:
        updated = 0
        not_found = []
        for _, row in filtered.iterrows():
            borough = db.query(Borough).filter_by(name=row["Name"]).first()
            if borough is None:
                not_found.append(row["Name"])
                continue
            borough.population = int(row["Population"])
            updated += 1

        db.commit()
        print(f"Updated {updated} boroughs.")
        if not_found:
            print(f"WARNING: no matching borough found for: {not_found}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

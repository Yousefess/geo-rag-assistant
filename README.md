# GeoRAG Assistant

AI-powered assistant combining Retrieval-Augmented Generation (RAG) over
urban planning documents with spatial queries on London geographic data.

**Status:** 🚧 In active development

## Stack
- FastAPI
- PostgreSQL + PostGIS + pgvector
- OpenRouter (LLM)

## Project Structure
See `docs/architecture.md` for design decisions.

## Data Setup

Raw data files are not committed to this repo (see `.gitignore`) since they're
large and publicly downloadable. To reproduce the dataset locally:

1. **London borough boundaries** (spatial data)
   - Source: [Statistical GIS Boundary Files for London](https://data.london.gov.uk/dataset/statistical-gis-boundaries-london) (London Datastore)
   - Download: `statistical-gis-boundaries-london.zip`
   - Extract and place the `ESRI/London_Borough_Excluding_MHW.shp` (+ companion
     files) at: `data/raw/london_boundaries/ESRI/`
   - Original CRS: British National Grid (EPSG:27700) — the ingestion script
     reprojects to WGS84 (EPSG:4326) to match our PostGIS column.

2. **Borough population** (statistical data)
   - Source: [Land Area and Population Density, Ward and Borough](https://data.london.gov.uk/dataset/land-area-and-population-density-ward-and-borough-e1zp8) (London Datastore)
   - Download: `Land Area & Population - Borough (CSV Version)`
   - Place at: `data/raw/borough_population.csv`
   - We use the **2010 ONS MYE** figures (the latest *actual* mid-year estimate
     before the dataset switches to GLA projections, which run through 2050).

### Running ingestion

```bash
python3 -m scripts.ingest_boroughs      # loads 33 borough boundaries
python3 -m scripts.update_population    # adds 2010 population figures
```

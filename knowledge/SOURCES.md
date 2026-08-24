# Phase 3 authoritative sources

The runtime ingestion pipeline reads `knowledge/sources.json` and fetches only
official WHO and CDC pages. Use `python -m rag.ingest --refresh` to create fresh
raw snapshots and regenerate `knowledge/corpus.json`.

| Publisher | Title | URL |
|---|---|---|
| WHO | Ultraviolet radiation | https://www.who.int/news-room/fact-sheets/detail/ultraviolet-radiation |
| WHO | Radiation: The ultraviolet (UV) index | https://www.who.int/news-room/questions-and-answers/item/radiation-the-ultraviolet-%28uv%29-index |
| WHO | Radiation: Protecting against skin cancer | https://www.who.int/news-room/questions-and-answers/item/radiation-protecting-against-skin-cancer |
| CDC | Sun Safety Facts | https://www.cdc.gov/skin-cancer/sun-safety/index.html |
| CDC | Ultraviolet Radiation | https://www.cdc.gov/radiation-health/features/uv-radiation.html |
| CDC | About Heat and Your Health | https://www.cdc.gov/extreme-heat/prevention/index.html |

The application is a decision-support prototype, not a medical diagnostic or
treatment system. Retrieved evidence constrains explanations but cannot
override deterministic safety policy.

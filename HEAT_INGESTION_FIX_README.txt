SunSafe AI — heat ingestion fix

Root cause:
- knowledge/sources.json already declared the CDC heat source.
- Direct requests to cdc.gov returned HTTP 403.
- Therefore the heat_safety source never entered knowledge/corpus.json.

Correction:
- Keep CDC as the authoritative publisher.
- Use the official CDC Stacks record for "Extreme heat: tips for preventing heat-related illness".
- Fetch its official CDC-hosted PDF via the CDC Stacks download URL.
- Add PDF extraction with pypdf.
- Preserve the public citation URL as the CDC Stacks record URL.
- Record fetch_url separately in ingestion errors when relevant.
- Do not alter the retrieval test or fabricate heat_safety evidence.

Validation order:
1. Replace rag/ingest.py and knowledge/sources.json.
2. Replace requirements.txt with the supplied version.
3. Install:
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
4. Rebuild:
   .\.venv\Scripts\python.exe -m rag.build_index --refresh
5. Confirm corpus contains heat_safety:
   .\.venv\Scripts\python.exe -c "import json; c=json.load(open('knowledge/corpus.json',encoding='utf-8')); print(len(c)); print(sorted(set(x['topic'] for x in c))); print(sum(x['topic']=='heat_safety' for x in c))"
6. Run:
   .\.venv\Scripts\python.exe -m pytest tests/test_rag_retriever.py -q
7. Then:
   .\.venv\Scripts\python.exe -m pytest -q
8. Finally rerun Phase 5 evaluations.

Do not modify tests to hide retrieval failures.
Do not commit .env or API keys.

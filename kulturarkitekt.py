#!/usr/bin/env python3
"""Kulturarkitekten – kobler kulturdata til Mistral Large via La Plateforme API.

Bruk:
  MISTRAL_API_KEY settes som miljøvariabel (aldri i kode/GitHub).
  python3 kulturarkitekt.py --demo   kjører analyse på demo-data uten nøkkel (mock)
"""
import os
import json
import urllib.request

API_URL = "https://api.mistral.ai/v1/chat/completions"
MODEL = "mistral-large-latest"

SYSTEM_PROMPT = """Du er Kulturarkitekten – en ekspert på organisasjonskultur, transformasjonsledelse
og forbedringskultur. Du får aggregerte, anonyme måledata og skal gi en kort, presis analyse på norsk bokmål.

Regler:
- Svar ALLTID på norsk bokmål.
- Aldri anta eller dikt opp enkeltpersoner – dataene er anonyme og aggregerte.
- Struktur svaret slik:
  1. Tre hovedfunn (maks 2 setninger hver)
  2. Svakeste dimensjon og hva det betyr i praksis
  3. To konkrete tiltak (SMART) med begrunnelse
  4. Én ting ledelsen bør følge med på ved neste måling
- Maks 250 ord totalt. Profesjonell, forskningsbasert tone."""


def bygg_prompt(stats: dict) -> str:
    dims = stats.get("dimensions", {})
    linjer = []
    for gruppe in ("tl", "fk"):
        for dim, s in dims.get(gruppe, {}).items():
            if s:
                linjer.append(f"- {gruppe.upper()} / {dim}: snitt {s['mean']} (n={s['n']})")
    return f"""Her er resultatene fra kulturkartleggingen (alle aggregerte, anonyme):

Antall svar: {stats.get('count')}
TL-indeks (transformasjonsledelse): {stats.get('tl_index')}
FK-indeks (forbedringskultur): {stats.get('fk_index')}
Korrelasjon TL↔FK: {stats.get('correlation')}

Dimensjoner (skala 1–5):
{chr(10).join(linjer)}

Gi analysen nå etter malen."""


def analyser(stats: dict, api_key: str | None = None) -> dict:
    """Kjør analyse via Mistral API. Returnerer {ok, tekst} eller {ok: False, error}."""
    key = api_key or os.environ.get("MISTRAL_API_KEY")
    if not key:
        return {"ok": False, "error": "MISTRAL_API_KEY mangler. Sett den som miljøvariabel: export MISTRAL_API_KEY=..."}
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": bygg_prompt(stats)},
        ],
        "temperature": 0.4,
        "max_tokens": 600,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
        return {"ok": True, "tekst": data["choices"][0]["message"]["content"], "model": MODEL}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def mock_analyse(stats: dict) -> dict:
    """Lokal test uten API-nøkkel."""
    return {"ok": True, "model": "mock", "tekst": (
        "1. Hovedfunn: Psykologisk trygghet er lav – det hemmer læring.\n"
        "2. Svakeste dimensjon: se data over; laveste snitt bør prioriteres.\n"
        "3. Tiltak: (a) lederopplæring i tilbakemelding, (b) ukentlig 'feiring av feil'-runde.\n"
        "4. Følg med på: om FK-indeksen stiger ved gjenmåling."
    )}


if __name__ == "__main__":
    import sys
    demo_stats = {"count": 118, "tl_index": 3.47, "fk_index": 3.37, "correlation": 0.85,
                  "dimensions": {"fk": {"psykologisk_trygghet": {"mean": 2.9, "n": 118}}}}
    if "--demo" in sys.argv:
        print(json.dumps(mock_analyse(demo_stats), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(analyser(demo_stats), ensure_ascii=False, indent=2))

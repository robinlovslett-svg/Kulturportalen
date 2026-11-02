# Kulturportalen

En portal for å måle og utvikle kulturen i et selskap, bygget på forskningen om
sammenhengen mellom **transformasjonsledelse (TL)** og **forbedringskultur (FK)**
(Løvslett & Militei, UiT, 2026).

## Hva portalen gjør

- **Spørreundersøkelse** med alle 20 påstander fra studien (8 om lederskap/TL, 12 om forbedringskultur/FK), 5-punkts Likert-skala, anonym.
- **Individuell tilbakemelding** etter innsending: totalskår for TL og FK, pluss skår per dimensjon.
- **Admin-dashboard** med aggregerte resultater: antall svar, gjennomsnitt, Pearsons korrelasjon TL–FK, trend per måned, gruppesammenligning (kjønn, ansiennitet, personalansvar) og CSV-eksport.

## Kjøring (kun Python 3, ingen pakker å installere)

```bash
python3 server.py
```

Deretter i nettleseren:

- `http://127.0.0.1:8000` – spørreundersøkelse
- `http://127.0.0.1:8000/admin` – resultater (admin)

Data lagres i `data/kulturportal.db` (SQLite). Slett filen for å starte på nytt.

## Filer

```
server.py          # backend: HTTP-server + SQLite + API
static/survey.*    # spørreskjema (forside)
static/result.html # individuell tilbakemelding
static/admin.*     # dashbord for aggregerte resultater
static/style.css
```

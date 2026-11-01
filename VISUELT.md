# Visuell iterasjon (internt verktøy)

`screenshot.py` tar skjermbilder av alle sider via headless Chromium (Playwright).

## Kjøring i sandbox
```bash
python3 server.py &          # portalen må kjøre
python3 screenshot.py        # lagrer PNG-er til /workspace/.vibe/shots/
```

## Arbeidsflyt
1. Jeg endrer kode → pusher til branch
2. Jeg kjører `screenshot.py` lokalt og analyserer bildene selv
3. Ser jeg noe rart → fikser umiddelbart og gjentar
4. Du ser resultatet automatisk via watch.sh + auto-refresh

Dette gjør at jeg nå *ser* hva jeg lager før du trenger å rapportere feil.

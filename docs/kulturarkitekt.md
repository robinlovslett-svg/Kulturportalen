# Kulturarkitekten – AI-lag (fase 3)

## Arkitektur
- `kulturarkitekt.py` – kobler til Mistral API (mistral-large-latest)
- `POST /api/ai-analyse` – kjører analyse på aggregerte data
- `GET /api/ai-analyse?mock=1` – lokal test uten nøkkel
- Seksjon «🧠 AI-analyse» øverst på `/admin`

## Oppsett
1. Få API-nøkkel: https://console.mistral.ai → API Keys
2. På serveren: `export MISTRAL_API_KEY=sk-...`
3. Klikk «Kjør AI-analyse» på /admin

## Personvern
- Kun aggregerte tall sendes til API – aldri rå kommentarer med navn
- Mistral lagrer ikke data ved API-bruk (EU-hosting)

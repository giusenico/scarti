# Scarti

Un blog settimanale di data journalism sull'economia italiana. Ogni lunedì una
pipeline scarica serie da ISTAT e Banca d'Italia, rileva le anomalie
statistiche, genera un report narrativo bilingue (IT/EN) e invia una newsletter
agli iscritti.

## Struttura

```
pipeline/    Python — fetch, detect, narrate, render, mail
site/        Astro 5 + React islands — il blog
supabase/    Schema DB per subscribers (double opt-in)
.github/     Workflow cron settimanale + CI
```

## Setup locale

### Pipeline

```bash
cd pipeline
python -m venv .venv && source .venv/bin/activate
pip install -e ".[detect,narrate,mail,subscribers,dev]"

cp ../.env.example ../.env
# compila ANTHROPIC_API_KEY, RESEND_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

scarti verify-catalog                              # elenca le serie
scarti discover --source istat --query inflazione  # trova dataflow id
# → compila sdmx_dataflow/sdmx_key in pipeline/src/scarti/catalog.yaml
scarti fetch istat.ipc.nic.general                 # smoke test di una serie
scarti run                                          # pipeline completa (no mail)
scarti run --send-mail                              # con newsletter
```

### Site

```bash
cd site
npm install
npm run dev         # http://localhost:4321
```

### Supabase

Esegui la migration `supabase/migrations/0001_subscribers.sql` nell'editor
SQL del tuo progetto Supabase.

## Deploy

- **Site**: Vercel, collegato al repo. Ogni push a `main` ridiployga.
- **Pipeline**: GitHub Actions esegue ogni lunedì 05:00 UTC, committa i nuovi
  file JSON in `site/src/content/reports/` e `site/src/data/series/`, il push
  ridiployga il sito, poi invia la newsletter via Resend.

Secrets richiesti in GitHub Actions:
`ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`.
Variables: `SCARTI_SITE_URL`, `SCARTI_FROM_EMAIL`.

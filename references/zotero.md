# Zotero integration notes

Use `scripts/zotero_profile.py` when Jun wants the radar to learn from an existing Zotero library.

## Default assumption

- Default DB path: `~/Zotero/zotero.sqlite`
- This may fail if Zotero stores the DB elsewhere or keeps it locked.

## Command

```bash
python3 skills/paper-radar/scripts/zotero_profile.py --top 80
```

## What it does

- Reads titles / abstracts / venue-ish fields from Zotero sqlite
- Extracts frequent terms
- Produces a lightweight JSON profile that can guide future ranking refinement

## Caveat

This is a practical bootstrap, not magic personalization. Real personalization should eventually combine:
- Zotero library terms
- explicit positive/negative keywords
- paper click/save history
- manual thumbs-up / thumbs-down feedback

# Standalone Policy Journal Tracker

This folder is prepared to be moved into an independent repository.

## What it does

- Tracks latest-issue TOC papers from 10 policy/public-administration/housing journals.
- Filters papers by three topics:
  - `房地产`
  - `城市治理`
  - `公共政策`
- Optionally translates titles/abstracts to Chinese using Kimi (`KIMI_API_KEY`).

## Structure

- `scripts/update_policy_tracker.py`: updater script
- `data/policy_tracker.json`: latest generated data

## Usage

Run from this folder:

```powershell
python scripts\update_policy_tracker.py
```

Optional env vars:

- `KIMI_API_KEY`
- `KIMI_MODEL` (default: `moonshot-v1-8k`)
- `MAX_POLICY_PAPERS_PER_JOURNAL` (default: `12`)
- `MAX_ABSTRACT_TRANSLATE_CHARS` (default: `2500`)


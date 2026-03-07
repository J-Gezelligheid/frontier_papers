# Standalone Econ Frontier Tracker

Tracks latest-issue TOC papers from economics top journals and field-top journals, then filters papers by these themes:

- 国际贸易
- 国际经济
- 产业经济
- 企业创新
- 医药产业
- 医疗创新
- 创新药

## Structure

- `scripts/update_econ_tracker.py`: updater script
- `data/econ_tracker.json`: generated data

## Usage

```powershell
python standalone-econ-frontier-tracker/scripts/update_econ_tracker.py
```

Optional env vars:

- `KIMI_API_KEY`
- `KIMI_MODEL` (default: `moonshot-v1-8k`)
- `MAX_ECON_PAPERS_PER_JOURNAL` (default: `12`)
- `MAX_ABSTRACT_TRANSLATE_CHARS` (default: `2500`)

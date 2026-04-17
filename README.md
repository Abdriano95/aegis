# aegis

A layered Python pipeline for automatic GDPR text classification.


### Miljösetup

```bash
git clone https://github.com/Abdriano95/aegis.git
cd aegis
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest --co -q
```
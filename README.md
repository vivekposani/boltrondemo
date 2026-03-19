# BizFlow Streamlit Cloud app (CSV-backed)

This package is ready for Streamlit Community Cloud. It does not require PostgreSQL. It reads a bundled CSV file at `data/blockloadprofile__nfms_audit_sample.csv`.

You can also upload a replacement CSV from the UI.

## Repository layout

- `app.py` — Streamlit entrypoint
- `requirements.txt` — Python dependencies
- `.streamlit/config.toml` — theme
- `data/blockloadprofile__nfms_audit_sample.csv` — static demo dataset

## Deploy to Streamlit Community Cloud

1. Create a public GitHub repository.
2. Upload these files to the repo root, keeping the `data/` and `.streamlit/` folders intact.
3. Sign in to Streamlit Community Cloud with GitHub.
4. Click **Deploy an app** and choose the repository and branch.
5. Set the main file path to `app.py`.
6. Deploy.

## CSV contract

Your own CSV should include these columns at minimum:
- `run_cycle`
- `final_failure_source`
- `retry_count`
- `final_status`
- `mdm_failure_category`
- `final_message`
- `device_id`
- `updated_ts`
- `deviated_flag`

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

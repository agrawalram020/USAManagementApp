# USAManagementApp

This is a Flask-based ERP system for Unity Shuttle Arena (badminton court management).

## New Revenue Agent Feature

A lightweight "agent" analyzes recent transaction data and suggests ways to increase revenue.

### How it works

- The agent collects statistics from the last 30 days of completed transactions (total revenue, breakdown by court/category).
- It uses OpenAI's API (if `OPENAI_API_KEY` is set in the environment) to generate three actionable suggestions, falling back to simple heuristics otherwise.
- The suggestions are displayed on a dedicated page accessible via the **Revenue Agent** link in the navbar (visible only to owners).

### Setup

1. Create a Python virtual environment and install dependencies:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. (Optional) Set your OpenAI API key to get intelligent responses:
   ```powershell
   setx OPENAI_API_KEY "your_key"
   ```
   Restart your shell afterwards.

3. Run the app:
   ```powershell
   py app.py
   ```

4. Log in with an owner account (e.g., `ram` / `unity77`) and click the **Revenue Agent** button.

### Usage

- Click **Run Analysis** to fetch suggestions.
- If OpenAI is configured, you'll see AI-generated recommendations; otherwise, default heuristic tips will appear.

### Notes

- The agent currently analyses a 30‑day window and is easily extensible.
- You can modify `gather_revenue_data` or the prompt in `revenue_agent_suggestions` to tailor the analysis.

---

Other parts of the app remain unchanged.

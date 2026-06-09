# Demand/Supply Market Intelligence Dashboard

FastAPI + static HTML dashboard for pulling on-demand stock data from Massive REST APIs.

## Project structure

```text
market_dashboard_config_refactor/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── clients/
│   │   ├── __init__.py
│   │   └── massive_client.py
│   └── services/
│       ├── __init__.py
│       └── stock_service.py
├── static/
│   └── index.html
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 1. Create and activate a virtual environment

Linux / EC2:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

## 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Create your `.env` file

Copy the example file:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
MASSIVE_API_KEY=your_actual_key_here
MASSIVE_BASE_URL=https://api.massive.com
```

If your Massive plan uses delayed data:

```env
MASSIVE_API_KEY=your_actual_key_here
MASSIVE_BASE_URL=https://delay.massive.com
```

## 4. Run the app

Because `main.py` now lives inside the `app` package, run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

```text
http://127.0.0.1:8000
```

On EC2, use:

```text
http://YOUR_PUBLIC_IP:8000
```

Make sure your EC2 security group allows inbound TCP traffic on port `8000`.

## 5. Health check

Open:

```text
http://127.0.0.1:8000/api/health
```

You should see:

```json
{
  "ok": true,
  "massive_api_key_configured": true,
  "massive_base_url": "https://api.massive.com"
}
```

## 6. API example

```text
http://127.0.0.1:8000/api/stocks?tickers=AAPL,MSFT,NVDA
```

The API accepts comma, semicolon, pipe, space, or newline-delimited tickers.

## Notes

Some Massive endpoints may be unavailable depending on your plan. The app handles that by showing endpoint-level failures in the dashboard's **Data Health** tab instead of crashing the whole dashboard.

The `Supply Chain Exposure` tab is a placeholder for the future module where market movement can be correlated with order book, supplier, backlog, inventory, and lead-time data.


spread = ask_price - bid_price
spread_pct = spread / mid_price
quote_imbalance = bid_size / (bid_size + ask_size)
trade_pressure = buyer/seller initiated estimate
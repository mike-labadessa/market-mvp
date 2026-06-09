# Market-MVP

Enterprise-grade market intelligence, financial analytics, portfolio research, machine learning, AI-assisted research, and future supply chain exposure platform.

Market-MVP is designed as a full-stack decision support system that combines market data, financial statements, valuation metrics, technical indicators, machine learning forecasts, market microstructure analysis, and AI-generated research into a unified platform.

The long-term vision is to evolve beyond traditional equity analysis into operational intelligence by integrating supply chain, inventory, procurement, logistics, and demand forecasting datasets to identify business risks and opportunities before they appear in financial statements.

This project demonstrates end-to-end ownership across:

- Data Engineering
- Backend Engineering
- Cloud Infrastructure
- Financial Analytics
- Machine Learning
- AI Integration
- Executive Decision Support Systems

The platform is designed as a foundation for future supply chain intelligence and operational risk analytics. Functionality that can be applied to other contexts.

---

# Project Objectives

* Build a production-style financial analytics platform
* Demonstrate end-to-end data engineering capabilities
* Showcase cloud-native architecture patterns
* Implement machine learning forecasting workflows
* Integrate multiple AI research providers
* Create executive decision-support tooling
* Establish a foundation for future supply chain intelligence

---


## Current Architecture

```text
                 ┌──────────────────┐
                 │   Market-MVP UI  │
                 │  HTML / JS       │
                 └─────────┬────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ FastAPI Backend  │
                 │ app.main         │
                 └─────────┬────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼

┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Massive APIs   │ │ OpenAI API     │ │ Gemini API     │
└────────────────┘ └────────────────┘ └────────────────┘
        │
        ▼

┌────────────────────────────────────┐
│ Data Integration Layer             │
├────────────────────────────────────┤
│ Overview                           │
│ Price History                      │
│ Fundamentals                       │
│ Ratios                             │
│ Dividends                          │
│ News                               │
│ Quotes                             │
│ Trades                             │
└────────────────────────────────────┘
        │
        ▼

┌────────────────────────────────────┐
│ Analytics Layer                    │
├────────────────────────────────────┤
│ RSI                                │
│ MACD                               │
│ Moving Averages                    │
│ Sharpe Ratio                       │
│ CAPM                               │
│ Correlation Matrix                 │
│ Portfolio Allocation               │
│ Supply/Demand Analysis             │
└────────────────────────────────────┘
        │
        ▼

┌────────────────────────────────────┐
│ Decision Support Layer             │
├────────────────────────────────────┤
│ Forecasting Models                 │
│ Risk Assessment                    │
│ Benchmark Analysis                 │
│ AI Research                        │
│ Portfolio Recommendations          │
└────────────────────────────────────┘
```

---

# Current Features

## Market Overview

* Multi-ticker analysis
* Market overview statistics
* News aggregation
* Price history
* Volume analysis

## Technical Analysis

* Interactive Plotly charts
* 20 Day Moving Average
* 50 Day Moving Average
* 200 Day Moving Average
* RSI
* MACD
* Current value dashboard

## Financial Fundamentals

Income Statement

* Revenue
* Gross Profit
* EBITDA
* Net Income
* Operating Income

Balance Sheet

* Assets
* Liabilities

Cash Flow

* Operating Cash Flow
* Investing Cash Flow
* Financing Cash Flow

## Financial Ratios

* P/E
* P/B
* P/S
* EV/EBITDA
* Debt / Equity
* Current Ratio
* Quick Ratio
* ROA
* ROE
* Dividend Yield
* Free Cash Flow

## Corporate Actions

* Dividend history
* Cash distributions
* Frequency tracking
* Split history

## News Intelligence

* Ticker-specific news
* Publisher metadata
* Sentiment metadata
* Direct article links

## AI Research

Parallel model analysis using:

* OpenAI
* Gemini

Research incorporates:

* Fundamentals
* Ratios
* Technical indicators
* News
* Market analytics
* Portfolio metrics

Outputs:

* Executive Summary
* Opportunities
* Risks
* Valuation Commentary
* Recommendation

## Financial ML Analysis

Portfolio Analytics

* Sharpe Ratio
* CAPM
* Alpha
* Beta
* Volatility
* Annualized Return
* Maximum Drawdown

Benchmarking

Market:

* SPY
* QQQ
* DIA
* IWM

Sectors:

* XLK
* XLF
* XLV
* XLY
* XLP
* XLE
* XLI
* XLB
* XLRE
* XLU
* XLC

Risk-Free Rate

FRED Integration:

* DGS3MO
* DGS10

Forecast Models

* Linear Regression
* Moving Average
* Exponential Smoothing
* Momentum
* Random Forest
* Gradient Boosting
* ARIMA

Outputs

* Correlation Matrix
* Portfolio Analytics
* Benchmark Analysis
* Allocation Recommendations
* Portfolio Allocation Pie Chart

## Bid / Ask Supply Demand

Market microstructure analytics

Metrics:

* Bid Price
* Ask Price
* Spread
* Spread %
* Bid Depth
* Ask Depth
* Trade Volume
* Quote Imbalance
* Trade Pressure

Signals:

* Bullish Supply Demand
* Bearish Supply Demand
* Balanced Depth
* Buy Pressure
* Sell Pressure

## Data Health Monitoring

Per-endpoint health reporting

* Success tracking
* Failure tracking
* Error visibility
* Resilient endpoint handling

---

# Skills Demonstrated

## Data Engineering

* Data ingestion pipelines
* API integration
* Data normalization
* Multi-source aggregation
* Schema harmonization
* Financial data modeling
* Data quality monitoring

## Backend Engineering

* Python
* FastAPI
* Async programming
* REST APIs
* Service-oriented architecture
* Configuration management
* Error handling and resiliency

## Financial Analytics

* Financial statement analysis
* Ratio analysis
* Market microstructure analysis
* Portfolio analytics
* Risk-adjusted performance measurement
* CAPM
* Sharpe Ratio

## Machine Learning

* Feature engineering
* Time-series forecasting
* Linear Regression
* ARIMA
* Random Forest
* Gradient Boosting
* Model evaluation

## AI Engineering

* OpenAI integration
* Gemini integration
* Multi-model orchestration
* Prompt engineering
* AI-assisted research generation

## Cloud Engineering

Current

* AWS EC2
* VPC Networking
* Linux Administration
* Security Groups
* Elastic IP

Future

* Docker
* Docker Compose
* Nginx
* ECS
* Fargate
* Kubernetes
* CI/CD

---

# Future Roadmap

## Supply Chain Exposure Engine

Future operational datasets:

* Purchase Orders
* Inventory
* Supplier Data
* Logistics Data
* Forecast Demand Data
* Manufacturing Capacity

Derived analytics:

* Supplier Concentration Risk
* Inventory Stress
* Demand Acceleration
* Margin Compression Risk
* Operational Exposure Scores

## AWS Data Engineering Architecture

Ingestion

* API Gateway
* Lambda
* Kinesis
* SQS

Storage

* S3
* Parquet
* Iceberg
* Delta Lake

Processing

* Glue
* Spark
* Airflow

Serving

* Athena
* Redshift
* PostgreSQL
* FastAPI

---

# Containerization Roadmap

## Docker

Future deployment architecture:

```text
Browser
   │
   ▼
Nginx Container
   │
   ▼
FastAPI Container
   │
   ├── Massive API
   ├── OpenAI API
   ├── Gemini API
   └── FRED API
```

Future files:

* Dockerfile
* docker-compose.yml
* nginx.conf

Production goals:

* Reproducible deployments
* Environment isolation
* Infrastructure portability
* Cloud-native scalability

---

# Disclaimer

Market-MVP provides research and decision-support analytics only.

This platform does not provide investment advice and should not be used as the sole basis for investment decisions.




# Quick Start

## Install

```bash
python -m venv .venv
pip install -r requirements.txt
```

## Configure

Create a .env file:

```env
MASSIVE_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
FRED_API_KEY=
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:

http://localhost:8000
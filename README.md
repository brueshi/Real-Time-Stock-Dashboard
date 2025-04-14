# Real-Time Stock Market Dashboard

## Overview
A dynamic, interactive dashboard for real-time stock market analysis built with Python and Dash. This application allows users to monitor and analyze stock performance through multiple visualization techniques and technical indicators for PLTR, TSLA, NVDA, TSM, and AAPL (configurable to other stocks).

![Screenshot 2025-04-14 105624](https://github.com/user-attachments/assets/2680bac1-6510-4aed-afac-6028240e305a)


## Features
- **Real-time Market Data**: Fetches financial data from Alpha Vantage API
- **Multi-tab Interface**: Overview, Individual Analysis, and Comparison views
- **Technical Analysis**: Moving averages, RSI, volatility metrics, volume analysis
- **Interactive Visualizations**: Customizable date ranges and metrics
- **Performance Comparison**: Compare stocks via normalized views, absolute price, returns
- **Data Caching**: Minimizes API calls with local storage
- **Mock Data Generation**: Generates realistic stock data when API limits are reached

## About the Data
This dashboard connects to Alpha Vantage API but includes a fallback system when API limits are reached:
- Attempts to retrieve real market data first
- Automatically generates notional data with realistic patterns if needed
- All visualizations work identically with both data sources

## Technology Stack
- **Python**, **Dash**, **Plotly**, **Pandas**, **Requests**, **NumPy**

## Installation and Setup
1. Download the file
2. Run in terminal: `python "file_path"`
3. Navigate to http://127.0.0.1:8050/ in your browser
4. Keep the terminal open while using

## Usage Guide
- **Overview Tab**: View comparative performance metrics for all stocks
- **Individual Analysis**: Select stock, date range, and technical indicators
- **Comparison Tab**: Compare multiple stocks using different metrics

## Data Engineering Highlights
- ETL pipeline for financial data
- Intelligent data caching
- Fallback systems for data continuity
- Real-time processing with error handling

## Future Enhancements
- Machine learning price predictions
- Portfolio tracking
- News integration
- Alert system for price movements

## Alpha Vantage API Key
For your own API key, sign up at [Alpha Vantage](https://www.alphavantage.co/support/#api-key) and replace the API_KEY variable in the code.

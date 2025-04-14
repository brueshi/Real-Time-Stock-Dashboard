import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime, timedelta, date
import time

# Configuration
API_KEY = "UUWX2H31I6QIMI2D"  # Replace with your actual API key
BASE_URL = 'https://www.alphavantage.co/query'
OUTPUT_FOLDER = "stock_data"
SYMBOLS = ["TSLA", "PLTR", "NVDA", "TSM", "AAPL"]

# Set the specific date range
START_DATE = date(2025, 3, 31)
END_DATE = date.today()

# Create output folder if it doesn't exist
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def fetch_daily_time_series(symbol, api_key):
    """Fetch daily time series data from Alpha Vantage API"""
    url = f'{BASE_URL}?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    
    print(f"Fetching data for {symbol}...")
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        return None
    
    data = response.json()
    
    # Check if error message is in the response
    if 'Error Message' in data:
        print(f"API Error for {symbol}: {data['Error Message']}")
        return None
    
    if 'Note' in data:
        print(f"API Note for {symbol}: {data['Note']}")
        # This likely means we've hit the API rate limit
    
    # Extract time series data
    time_series = data.get('Time Series (Daily)')
    
    if not time_series:
        print(f"No time series data found for {symbol}")
        # Generate mock data for demo purposes
        return generate_mock_data(symbol)
    
    # Convert to DataFrame
    df = pd.DataFrame.from_dict(time_series, orient='index')
    
    # Rename columns
    df.columns = [col.split('. ')[1] for col in df.columns]
    
    # Convert string values to float
    for col in df.columns:
        df[col] = df[col].astype(float)
    
    # Add date as a column
    df['date'] = pd.to_datetime(df.index)
    df.reset_index(drop=True, inplace=True)
    
    # Sort by date (ascending)
    df = df.sort_values('date')
    
    return df

def generate_mock_data(symbol):
    """Generate mock stock data for demo purposes when API fails"""
    print(f"Generating mock data for {symbol}")
    
    # Create date range from 1 year ago to today
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    
    # Set seed based on symbol for consistent but different data
    seed = sum(ord(c) for c in symbol)
    np.random.seed(seed)
    
    # Generate base price and daily variations
    base_price = np.random.uniform(50, 500)
    
    # Generate daily price movements with some trending behavior
    n = len(dates)
    trend = np.cumsum(np.random.normal(0.0005, 0.015, n))
    noise = np.random.normal(0, 0.02, n)
    
    # Create price series with seasonality
    price_series = base_price * (1 + trend + noise)
    
    # Ensure prices are positive
    price_series = np.maximum(price_series, 0.1)
    
    # Generate volume
    volume = np.random.randint(1000000, 50000000, n)
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'open': price_series * np.random.uniform(0.99, 1.01, n),
        'high': price_series * np.random.uniform(1.01, 1.05, n),
        'low': price_series * np.random.uniform(0.95, 0.99, n),
        'close': price_series,
        'volume': volume
    })
    
    return df

def save_data(df, symbol, folder=OUTPUT_FOLDER):
    """Save the DataFrame to a CSV file"""
    filename = f"{folder}/{symbol}_daily.csv"
    df.to_csv(filename, index=False)
    return filename

def load_data(symbol, folder=OUTPUT_FOLDER):
    """Load data from CSV file"""
    filename = f"{folder}/{symbol}_daily.csv"
    if os.path.exists(filename):
        return pd.read_csv(filename, parse_dates=['date'])
    return None

def is_data_stale(symbol, max_age_days=1, folder=OUTPUT_FOLDER):
    """Check if local data is stale"""
    filename = f"{folder}/{symbol}_daily.csv"
    if not os.path.exists(filename):
        return True
    
    file_mtime = datetime.fromtimestamp(os.path.getmtime(filename))
    current_time = datetime.now()
    
    return (current_time - file_mtime).days >= max_age_days

def calculate_metrics(df):
    """Calculate various technical indicators"""
    # Daily returns
    df['daily_return'] = df['close'].pct_change() * 100
    
    # Moving averages
    df['MA_20'] = df['close'].rolling(window=20).mean()
    df['MA_50'] = df['close'].rolling(window=50).mean()
    
    # Volatility (30-day rolling standard deviation)
    df['volatility_30d'] = df['daily_return'].rolling(window=30).std()
    
    # RSI (14-day)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Avoid division by zero
    loss = loss.replace(0, np.nan)
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Fill NaN values
    df = df.fillna(method='bfill')
    
    return df

def process_stock_data(symbols, api_key, force_refresh=False):
    """Process data for multiple stocks"""
    results = {}
    
    for i, symbol in enumerate(symbols):
        # Check if we need to refresh the data
        need_refresh = force_refresh or is_data_stale(symbol)
        
        # Try to load existing data first
        df = load_data(symbol)
        
        # Fetch new data if needed
        if df is None or need_refresh:
            df = fetch_daily_time_series(symbol, api_key)
            
            if df is not None:
                save_data(df, symbol)
            
            # Add delay for API rate limiting
            if i < len(symbols) - 1:
                time.sleep(15)
        
        if df is not None:
            # Calculate metrics
            df = calculate_metrics(df)
            results[symbol] = df
    
    return results

# Process stock data
stock_data = process_stock_data(SYMBOLS, API_KEY)

# Initialize the Dash app
app = dash.Dash(__name__)
app.title = "Stock Analysis Dashboard"

# Define app layout
app.layout = html.Div([
    html.H1("Stock Analysis Dashboard", className="header-title"),
    
    html.Div([
        # Tab selection
        dcc.Tabs(id="tabs", value="tab-overview", children=[
            dcc.Tab(label="Overview", value="tab-overview"),
            dcc.Tab(label="Individual Analysis", value="tab-individual"),
            dcc.Tab(label="Comparison", value="tab-comparison"),
        ]),
        
        # Tab content
        html.Div(id="tabs-content")
    ], className="dashboard-container")
], className="app-container")

# Tab content generator functions
def generate_overview_tab():
    # Get latest data for all stocks
    overview_data = []
    
    for symbol, df in stock_data.items():
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            
            # Calculate return since START_DATE
            start_data = df[df['date'] >= pd.Timestamp(START_DATE)]
            if not start_data.empty:
                start_price = start_data.iloc[0]['close']
                current_price = latest['close']
                period_return = ((current_price / start_price) - 1) * 100
            else:
                period_return = None
            
            overview_data.append({
                'Symbol': symbol,
                'Price': round(latest['close'], 2),
                'Daily Change': f"{round(latest['daily_return'], 2)}%" if 'daily_return' in latest and not pd.isna(latest['daily_return']) else "N/A",
                'Return Since Mar 31': f"{round(period_return, 2)}%" if period_return is not None else "N/A",
                'RSI': round(latest['RSI'], 2) if 'RSI' in latest and not pd.isna(latest['RSI']) else "N/A"
            })
    
    if not overview_data:
        return html.Div("No data available")
    
    # Create a table
    table_header = [html.Tr([html.Th(col) for col in overview_data[0].keys()])]
    table_rows = [html.Tr([html.Td(row[col]) for col in row.keys()]) for row in overview_data]
    
    table = html.Table(table_header + table_rows, className="stock-table")
    
    # Create a returns bar chart
    returns_data = [
        {'Symbol': row['Symbol'], 'Return': float(row['Return Since Mar 31'].replace('%', '')) if row['Return Since Mar 31'] != "N/A" else 0}
        for row in overview_data
    ]
    
    returns_fig = go.Figure(data=[
        go.Bar(
            x=[item['Symbol'] for item in returns_data],
            y=[item['Return'] for item in returns_data],
            marker_color='lightskyblue'
        )
    ])
    
    returns_fig.update_layout(
        title="Returns Since March 31, 2025",
        xaxis_title="Symbol",
        yaxis_title="Return (%)",
        height=400
    )
    
    return html.Div([
        html.H2("Market Overview"),
        html.Div(f"Data from {START_DATE} to {END_DATE}", className="date-range"),
        html.Div([
            dcc.Graph(figure=returns_fig)
        ], className="chart-container"),
        html.H3("Stock Summary"),
        table
    ])

def generate_individual_tab():
    return html.Div([
        html.Div([
            # Controls
            html.Div([
                html.Label("Select Stock:"),
                dcc.Dropdown(
                    id='stock-dropdown',
                    options=[{'label': symbol, 'value': symbol} for symbol in stock_data.keys()],
                    value=list(stock_data.keys())[0] if stock_data else None
                ),
                
                html.Label("Select Date Range:"),
                dcc.DatePickerRange(
                    id='date-range',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=END_DATE,
                    start_date=START_DATE,
                    end_date=END_DATE
                ),
                
                html.Label("Select Indicators:"),
                dcc.Checklist(
                    id='indicators-checklist',
                    options=[
                        {'label': 'Moving Averages', 'value': 'ma'},
                        {'label': 'Volume', 'value': 'volume'},
                        {'label': 'RSI', 'value': 'rsi'}
                    ],
                    value=['ma']
                )
            ], className="controls-container"),
            
            # Charts
            html.Div(id="individual-charts", className="charts-container")
        ])
    ])

def generate_comparison_tab():
    return html.Div([
        html.Div([
            # Controls
            html.Div([
                html.Label("Select Stocks:"),
                dcc.Dropdown(
                    id='stocks-multi-dropdown',
                    options=[{'label': symbol, 'value': symbol} for symbol in stock_data.keys()],
                    value=[list(stock_data.keys())[0]] if stock_data else [],
                    multi=True
                ),
                
                html.Label("Select Date Range:"),
                dcc.DatePickerRange(
                    id='comparison-date-range',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=END_DATE,
                    start_date=START_DATE,
                    end_date=END_DATE
                ),
                
                html.Label("Comparison Type:"),
                dcc.RadioItems(
                    id='comparison-type',
                    options=[
                        {'label': 'Price', 'value': 'price'},
                        {'label': 'Normalized', 'value': 'normalized'},
                        {'label': 'Returns', 'value': 'returns'}
                    ],
                    value='normalized'
                )
            ], className="controls-container"),
            
            # Comparison chart
            html.Div(id="comparison-chart", className="charts-container")
        ])
    ])

# Callback to update the tab content
@app.callback(
    Output("tabs-content", "children"),
    Input("tabs", "value")
)
def update_tab(tab):
    if tab == "tab-overview":
        return generate_overview_tab()
    elif tab == "tab-individual":
        return generate_individual_tab()
    elif tab == "tab-comparison":
        return generate_comparison_tab()

# Callback for individual stock analysis
@app.callback(
    Output("individual-charts", "children"),
    [Input("stock-dropdown", "value"),
     Input("date-range", "start_date"),
     Input("date-range", "end_date"),
     Input("indicators-checklist", "value")]
)
def update_individual_charts(symbol, start_date, end_date, indicators):
    if not symbol or not start_date or not end_date:
        return html.Div("Please select a stock and date range")
    
    # Get stock data
    df = stock_data.get(symbol)
    if df is None or df.empty:
        return html.Div(f"No data available for {symbol}")
    
    # Filter by date range
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    filtered_df = df[(df['date'] >= start) & (df['date'] <= end)]
    
    if filtered_df.empty:
        return html.Div(f"No data available for {symbol} in the selected date range")
    
    charts = []
    
    # Price chart
    price_fig = go.Figure()
    
    # Add price line
    price_fig.add_trace(
        go.Scatter(
            x=filtered_df['date'],
            y=filtered_df['close'],
            mode='lines',
            name=f'{symbol} Price'
        )
    )
    
    # Add Moving Averages if selected
    if 'ma' in indicators:
        if 'MA_20' in filtered_df.columns:
            price_fig.add_trace(
                go.Scatter(
                    x=filtered_df['date'],
                    y=filtered_df['MA_20'],
                    mode='lines',
                    name='20-day MA',
                    line=dict(color='orange', width=1)
                )
            )
        
        if 'MA_50' in filtered_df.columns:
            price_fig.add_trace(
                go.Scatter(
                    x=filtered_df['date'],
                    y=filtered_df['MA_50'],
                    mode='lines',
                    name='50-day MA',
                    line=dict(color='red', width=1)
                )
            )
    
    price_fig.update_layout(
        title=f"{symbol} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        height=400
    )
    
    charts.append(dcc.Graph(figure=price_fig))
    
    # Volume chart if selected
    if 'volume' in indicators:
        volume_fig = go.Figure()
        
        volume_fig.add_trace(
            go.Bar(
                x=filtered_df['date'],
                y=filtered_df['volume'],
                name='Volume'
            )
        )
        
        volume_fig.update_layout(
            title=f"{symbol} Trading Volume",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=300
        )
        
        charts.append(dcc.Graph(figure=volume_fig))
    
    # RSI chart if selected
    if 'rsi' in indicators and 'RSI' in filtered_df.columns:
        rsi_fig = go.Figure()
        
        rsi_fig.add_trace(
            go.Scatter(
                x=filtered_df['date'],
                y=filtered_df['RSI'],
                mode='lines',
                name='RSI'
            )
        )
        
        # Add overbought/oversold lines
        rsi_fig.add_shape(
            type="line", x0=filtered_df['date'].iloc[0], y0=70, 
            x1=filtered_df['date'].iloc[-1], y1=70,
            line=dict(color="red", dash="dash")
        )
        
        rsi_fig.add_shape(
            type="line", x0=filtered_df['date'].iloc[0], y0=30, 
            x1=filtered_df['date'].iloc[-1], y1=30,
            line=dict(color="green", dash="dash")
        )
        
        rsi_fig.update_layout(
            title=f"{symbol} RSI (14-day)",
            xaxis_title="Date",
            yaxis_title="RSI",
            yaxis=dict(range=[0, 100]),
            height=300
        )
        
        charts.append(dcc.Graph(figure=rsi_fig))
    
    return charts

# Callback for stock comparison
@app.callback(
    Output("comparison-chart", "children"),
    [Input("stocks-multi-dropdown", "value"),
     Input("comparison-date-range", "start_date"),
     Input("comparison-date-range", "end_date"),
     Input("comparison-type", "value")]
)
def update_comparison_chart(symbols, start_date, end_date, comp_type):
    if not symbols or not start_date or not end_date:
        return html.Div("Please select at least one stock and a date range")
    
    # Filter data by date range
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    
    comparison_fig = go.Figure()
    
    for symbol in symbols:
        df = stock_data.get(symbol)
        if df is None or df.empty:
            continue
        
        filtered_df = df[(df['date'] >= start) & (df['date'] <= end)]
        if filtered_df.empty:
            continue
        
        if comp_type == 'price':
            # Regular price
            comparison_fig.add_trace(
                go.Scatter(
                    x=filtered_df['date'],
                    y=filtered_df['close'],
                    mode='lines',
                    name=symbol
                )
            )
            y_title = "Price (USD)"
            title = "Stock Price Comparison"
            
        elif comp_type == 'normalized':
            # Normalize to 100 at start
            start_price = filtered_df['close'].iloc[0]
            normalized = filtered_df['close'] / start_price * 100
            
            comparison_fig.add_trace(
                go.Scatter(
                    x=filtered_df['date'],
                    y=normalized,
                    mode='lines',
                    name=symbol
                )
            )
            y_title = "Normalized Price (Base=100)"
            title = "Normalized Price Comparison"
            
        elif comp_type == 'returns':
            # Cumulative returns
            if 'daily_return' in filtered_df.columns:
                cumulative_return = (1 + filtered_df['daily_return'] / 100).cumprod() * 100 - 100
                
                comparison_fig.add_trace(
                    go.Scatter(
                        x=filtered_df['date'],
                        y=cumulative_return,
                        mode='lines',
                        name=symbol
                    )
                )
                y_title = "Cumulative Return (%)"
                title = "Cumulative Return Comparison"
    
    comparison_fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title=y_title,
        height=500
    )
    
    return dcc.Graph(figure=comparison_fig)

# Add some CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .app-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            
            .header-title {
                text-align: center;
                color: #2c3e50;
                margin-bottom: 30px;
            }
            
            .dashboard-container {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .controls-container {
                margin-bottom: 20px;
                padding: 15px;
                background-color: #ffffff;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .charts-container {
                background-color: #ffffff;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .stock-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            .stock-table th, .stock-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }
            
            .stock-table th {
                background-color: #4CAF50;
                color: white;
            }
            
            .stock-table tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            
            .date-range {
                text-align: center;
                margin-bottom: 20px;
                font-style: italic;
                color: #666;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the app
if __name__ == '__main__':
    app.run(debug=True)  # Updated from app.run_server(debug=True)
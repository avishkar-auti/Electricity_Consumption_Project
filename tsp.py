import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objs as go
import random
import time
from threading import Thread
from datetime import datetime, timedelta
import os

app = dash.Dash(__name__)

def add_random_data():
    while True:
        df = pd.read_csv('Datasets/electricity_data.csv')
        
        if os.path.exists('Datasets/device_consumption.csv') and os.path.getsize('Datasets/device_consumption.csv') > 0:
            df_device = pd.read_csv('Datasets/device_consumption.csv')
        else:
            df_device = pd.DataFrame(columns=['Date', 'Fridge', 'Kitchen Appliances', 'AC', 'Washing Machine', 'Other Appliances', 'Total_Consumption'])
        
        if df.empty:
            last_date = datetime.strptime('2019-01-01', '%Y-%m-%d')
        else:
            last_date = datetime.strptime(df.iloc[-1]['Date'], '%Y-%m-%d')
        
        new_date = last_date + timedelta(days=1)
        
        if new_date.strftime('%Y-%m-%d') in df['Date'].values:
            continue
        
        new_value = round(random.uniform(10, 23), 1)
        new_data = {'Date': new_date.strftime('%Y-%m-%d'), 'Total_Consumption': new_value}
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        proportions = [random.uniform(0.1, 0.3) for _ in range(5)]
        total_proportion = sum(proportions)
        proportions = [p / total_proportion for p in proportions]
        
        device_consumption = {
            'Date': new_date.strftime('%Y-%m-%d'),
            'Fridge': round(new_value * proportions[0], 1),
            'Kitchen Appliances': round(new_value * proportions[1], 1),
            'AC': round(new_value * proportions[2], 1),
            'Washing Machine': round(new_value * proportions[3], 1),
            'Other Appliances': round(new_value * proportions[4], 1)
        }
        
        device_total = sum(device_consumption[device] for device in device_consumption if device != 'Date')
        adjustment = round(new_value - device_total, 1)
        
        if adjustment != 0:
            device_consumption['Other Appliances'] += adjustment
        
        device_consumption['Total_Consumption'] = sum(device_consumption[device] for device in device_consumption if device != 'Date')

        df_device = pd.concat([df_device, pd.DataFrame([device_consumption])], ignore_index=True)
        
        df.to_csv('Datasets/electricity_data.csv', index=False)
        df_device.to_csv('Datasets/device_consumption.csv', index=False)
        
        time.sleep(3)

thread = Thread(target=add_random_data)
thread.daemon = True
thread.start()

app.layout = html.Div([
    html.H1("Live Time Series Graph"),
    dcc.Graph(id='timeseries-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    ),
    html.H1("Device-wise Consumption Pie Chart"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[],
        placeholder="Select a year",
        value=datetime.now().year
    ),
    dcc.Dropdown(
        id='month-dropdown',
        options=[
            {'label': 'January', 'value': '01'},
            {'label': 'February', 'value': '02'},
            {'label': 'March', 'value': '03'},
            {'label': 'April', 'value': '04'},
            {'label': 'May', 'value': '05'},
            {'label': 'June', 'value': '06'},
            {'label': 'July', 'value': '07'},
            {'label': 'August', 'value': '08'},
            {'label': 'September', 'value': '09'},
            {'label': 'October', 'value': '10'},
            {'label': 'November', 'value': '11'},
            {'label': 'December', 'value': '12'}
        ],
        placeholder="Select a month",
        value='01'
    ),
    dcc.Graph(id='pie-chart')
])

@app.callback(
    Output('timeseries-graph', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_timeseries(n):
    df = pd.read_csv('Datasets/electricity_data.csv')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Total_Consumption'],
        mode='lines+markers',
        name='Electricity Consumption',
        line_color="#19E2C5"
    ))
    fig.update_layout(
        title='Electricity Consumption Over Time',
        xaxis_title='Date',
        yaxis_title='Total Consumption'
    )
    return fig

@app.callback(
    Output('year-dropdown', 'options'),
    [Input('interval-component', 'n_intervals')]
)
def update_year_dropdown(n):
    df_device = pd.read_csv('Datasets/device_consumption.csv')
    df_device['Date'] = pd.to_datetime(df_device['Date'])
    years = df_device['Date'].dt.year.unique()
    return [{'label': str(year), 'value': year} for year in years]

@app.callback(
    Output('pie-chart', 'figure'),
    Output('total-consumption-text', 'children'),
    [Input('year-dropdown', 'value'), Input('month-dropdown', 'value')]
)
def update_pie_chart(selected_year, selected_month):
    if selected_year is None or selected_month is None:
        return go.Figure(), "Total Consumption: N/A"

    df_device = pd.read_csv('Datasets/device_consumption.csv')
    df_device['Date'] = pd.to_datetime(df_device['Date'])
    df_device['Month'] = df_device['Date'].dt.month
    df_device['Year'] = df_device['Date'].dt.year
    
    selected_data = df_device[(df_device['Year'] == selected_year) & (df_device['Month'] == int(selected_month))]
    
    if selected_data.empty:
        return go.Figure(), "Total Consumption: N/A"

    # Exclude non-numeric columns before performing the sum operation
    numeric_data = selected_data.drop(columns=['Date', 'Year', 'Month', 'Total_Consumption'])
    monthly_data = numeric_data.sum().reset_index()
    monthly_data.columns = ['Device', 'Consumption']
    
    total_consumption = selected_data['Total_Consumption'].sum()
    
    labels = monthly_data['Device']
    values = monthly_data['Consumption']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3
    )])
    
    month_name = datetime.strptime(selected_month, "%m").strftime("%B")
    fig.update_layout(
        title=f'{month_name} {selected_year} Device-wise Consumption'
    )
    
    total_consumption_text = f"Total Consumption: {total_consumption:.1f} kWh"
    
    return fig, total_consumption_text

app.layout = html.Div([
    html.H1("Live Time Series Graph"),
    dcc.Graph(id='timeseries-graph'),
    dcc.Interval(
        id='interval-component',
        interval=1*1000,
        n_intervals=0
    ),
    html.H1("Device-wise Consumption Pie Chart"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[],
        placeholder="Select a year",
        value=datetime.now().year
    ),
    dcc.Dropdown(
        id='month-dropdown',
        options=[
            {'label': 'January', 'value': '01'},
            {'label': 'February', 'value': '02'},
            {'label': 'March', 'value': '03'},
            {'label': 'April', 'value': '04'},
            {'label': 'May', 'value': '05'},
            {'label': 'June', 'value': '06'},
            {'label': 'July', 'value': '07'},
            {'label': 'August', 'value': '08'},
            {'label': 'September', 'value': '09'},
            {'label': 'October', 'value': '10'},
            {'label': 'November', 'value': '11'},
            {'label': 'December', 'value': '12'}
        ],
        placeholder="Select a month",
        value='01'
    ),
    dcc.Graph(id='pie-chart'),
    html.Div(id='total-consumption-text', style={'fontSize': 24, 'marginTop': 20})
])

if __name__ == '__main__':
    app.run_server(debug=True)

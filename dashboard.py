import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os
import dash_bootstrap_components as dbc

# 1. CONFIGURATION AND DATA LOADING 

# Path configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
# We assume the 'results' folder is in the same directory as this script.
# The script directory is therefore the project root.
project_root = script_dir
data_path = os.path.join(project_root, "results", "forecast_2030", "graph_forecast_data.csv")

# Load data
try:
    df = pd.read_csv(data_path)
    print("Graph data loaded successfully.")
except FileNotFoundError:
    print(f"Error: 'graph_forecast_data.csv' file not found at: {data_path}")
    print("Please run the 'forecast_to_2030.py' script first to generate this file.")
    exit()

# List of countries and indicators
countries = df['Country'].unique()
indicators = df['Indicator'].unique()

# Create grouped options for dropdown menus by SDG
# Filter to keep only indicators actually present in the data
indicator_groups = {
    "SDG 8: Decent Work and Economic Growth": [ind for ind in ['Real_GDP_Per_Capita', 'Unemployment_Rate', 'NEET_Rate'] if ind in indicators],
    "SDG 10: Reduced Inequalities": [ind for ind in ['Income_Distribution_Ratio', 'Income_Share_Bottom_40'] if ind in indicators],
    "SDG 13: Climate Action": [ind for ind in ['GHG_Emissions', 'Renewable_Energy_Share'] if ind in indicators]
}

# Define targets and business rules as a global constant to avoid redundancy
TARGETS_2030 = {
    'Real_GDP_Per_Capita': {'value': None, 'goal': 'higher_is_better'},
    'NEET_Rate': {'value': 9.0, 'goal': 'lower_is_better'},
    'Unemployment_Rate': {'value': 5.0, 'goal': 'lower_is_better'},
    'Income_Distribution_Ratio': {'value': None, 'goal': 'lower_is_better'},
    'Income_Share_Bottom_40': {'value': None, 'goal': 'higher_is_better'},
    'Renewable_Energy_Share': {'value': 42.5, 'goal': 'higher_is_better'},
    'GHG_Emissions': {'value': None, 'goal': 'lower_is_better'}
}

# 2. DASH APPLICATION INITIALIZATION 

app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR])
app.title = "Socio-Economic Forecasts 2030"

# 3. LAYOUT DEFINITION 

app.layout = dbc.Container(fluid=True, className="p-4", children=[
    # Main Title
    html.H1(
        children='Socio-Economic Forecasts Dashboard for 2030',
        className="text-center mb-4 text-primary"
    ),

    # SDG Descriptions
    dbc.Card(
        dbc.CardBody([
            html.P("This dashboard provides forecasts up to 2030 for key socio-economic indicators related to three United Nations Sustainable Development Goals (SDGs):", className="text-center"),
            dbc.Row([
                dbc.Col(html.Div(" SDG 8: Promote sustained, inclusive and sustainable economic growth, full and productive employment and decent work for all.", className="text-center")),
                dbc.Col(html.Div(" SDG 10: Reduce inequality within and among countries.", className="text-center")),
                dbc.Col(html.Div(" SDG 13: Take urgent action to combat climate change and its impacts.", className="text-center")),
            ], className="mt-3"),
        ]), color="primary", inverse=True, className="mb-4"
    ),

    html.Hr(),

    # Main Section with Side-by-Side Map and Graph 
    dbc.Row([
        # Left column for the map
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H4("European Overview for 2030", className="card-title text-center"),
                html.P("Select an indicator to visualize its 2030 forecast on the map.", className="text-center text-muted"),
                html.Div([
                    dcc.Dropdown(
                        id='sdg-dropdown',
                        options=[{'label': sdg, 'value': sdg} for sdg in indicator_groups.keys()],
                        placeholder="1. Select an SDG",
                    ),
                    dcc.Dropdown(
                        id='map-indicator-dropdown',
                        placeholder="2. Select an Indicator",
                    ),
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px', 'marginBottom': '20px'}),
                dcc.Loading(
                    type="default",
                    children=dcc.Graph(
                        id='europe-map',
                        style={'height': '65vh'},
                        config={'scrollZoom': False, 'displayModeBar': False}
                    )
                ),
                html.Div(id='map-legend', className="text-center mt-3"),
            ]), className="h-100")
        ], id='map-column', width=12), 

        # Right column for the trend graph
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H4("Detailed Analysis by Country", className="card-title text-center"),
                html.P("Click a country on the map or select it below.", className="text-center text-muted"),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': country, 'value': country} for country in countries],
                ),
                dcc.Loading(
                    type="default",
                    children=dcc.Graph(id='indicator-graphs', style={'height': '65vh'})
                ),
            ]), className="h-100")
        ], id='graph-column', width=5, style={'display': 'none'}), # The graph column is hidden by default
    ])
])

# 4. INTERACTIVITY DEFINITION (CALLBACKS) 

@app.callback(
    [Output('map-column', 'width'),
     Output('graph-column', 'style')],
    [Input('europe-map', 'clickData'),
     Input('map-indicator-dropdown', 'value')]
)
def toggle_graph_view(clickData, selected_indicator):
    """Shows or hides the graph and adjusts the layout."""
    # If no indicator is selected, always hide the graph
    if selected_indicator is None:
        return 12, {'display': 'none'}
    # If an indicator is selected AND a country is clicked, show the graph
    if clickData is not None:
        return 7, {'display': 'block', 'height': '100%'}
    # Otherwise (indicator selected but no click), keep graph hidden
    return 12, {'display': 'none'}

@app.callback(
    Output('map-indicator-dropdown', 'options'),
    Input('sdg-dropdown', 'value')
)
def set_indicator_options(selected_sdg):
    """Updates indicator menu options based on the selected SDG."""
    if not selected_sdg:
        return []
    # Only propose indicators that exist in the DataFrame
    available_indicators = indicator_groups[selected_sdg]
    if not available_indicators:
        return [{'label': 'No indicators available for this SDG', 'value': '', 'disabled': True}]
    return [{'label': indicator.replace('_', ' '), 'value': indicator} for indicator in available_indicators]

@app.callback(
    Output('europe-map', 'figure'),
    Input('map-indicator-dropdown', 'value')
)
def update_map(selected_indicator):
    """Updates the choropleth map based on the selected indicator."""
    # If no indicator is selected (on startup), do nothing
    if selected_indicator is None:
        # Display a blank map with a prompt
        fig = go.Figure(go.Scattergeo()) # Initialize with an empty geographic trace
        fig.update_layout(
            title_text="Select an SDG and an Indicator to display data",
            title_x=0.5,
            template="plotly_white",
            geo=dict(
                scope='europe',
                showframe=False,
                showcoastlines=True,
                landcolor='rgb(230, 230, 230)',
                lataxis_range=[36, 70], # Vertical zoom
                lonaxis_range=[-25, 45], # Horizontal zoom
                projection_type='mercator'
            ),
            margin={"r":0,"t":40,"l":0,"b":0},
            paper_bgcolor='rgba(0,0,0,0)', # Make the chart background transparent
        )
        return fig

    # Filter data for the year 2030 and the chosen indicator
    df_2030 = df[(df['Year'] == 2030) & (df['Indicator'] == selected_indicator)]

    # ERROR HANDLING 
    # If the dataframe is empty (no data for this indicator), return an empty figure
    if df_2030.empty:
        # Do not modify the map if data is not ready
        fig = go.Figure()
        fig.update_layout(title_text=f"No forecast data for: {selected_indicator.replace('_', ' ')}", title_x=0.5)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    # classification
    targets_2030 = {
        'Real_GDP_Per_Capita': {'value': None, 'goal': 'higher_is_better'},
        'NEET_Rate': {'value': 9.0, 'goal': 'lower_is_better'},
        'Unemployment_Rate': {'value': 5.0, 'goal': 'lower_is_better'},
        'Income_Distribution_Ratio': {'value': None, 'goal': 'lower_is_better'},
        'Income_Share_Bottom_40': {'value': None, 'goal': 'higher_is_better'},
        'Renewable_Energy_Share': {'value': 42.5, 'goal': 'higher_is_better'},
        'GHG_Emissions': {'value': None, 'goal': 'lower_is_better'}
    }

    def get_status_category(row):
        indicator = row['Indicator']
        forecast_value = row['Forecast_Value']
        # Retrieve the last actual value (2022) for this country and indicator
        last_value_series = df[(df['Country'] == row['Country']) & (df['Indicator'] == indicator) & (df['Year'] == 2022)]['Actual_Value']
        if last_value_series.empty:
            return 1 # Default to Orange if 2022 data is missing
        last_value = last_value_series.iloc[0]

        target_info = TARGETS_2030[indicator]
        
        # Logic for indicators with a numerical target
        if target_info['value'] is not None:
            is_met = (target_info['goal'] == 'lower_is_better' and forecast_value <= target_info['value']) or \
                     (target_info['goal'] == 'higher_is_better' and forecast_value >= target_info['value'])
            if is_met:
                return 0 # Green
            else:
                is_improving = (target_info['goal'] == 'lower_is_better' and forecast_value < last_value) or \
                               (target_info['goal'] == 'higher_is_better' and forecast_value > last_value)
                return 1 if is_improving else 2 # Orange or Red
        
        # Logic for indicators based on trend
        else:
            if indicator == 'Real_GDP_Per_Capita':
                growth_pct = ((forecast_value - last_value) / last_value) * 100 if last_value != 0 else 0
                if growth_pct > 10: return 0 # Green
                elif growth_pct >= 5: return 1 # Orange
                else: return 2 # Red
            else: # Other trend indicators
                is_good_trend = (target_info['goal'] == 'lower_is_better' and forecast_value < last_value) or \
                                (target_info['goal'] == 'higher_is_better' and forecast_value > last_value)
                return 0 if is_good_trend else 2 # Green or Red (no Orange for these cases)

    df_2030['Category'] = df_2030.apply(get_status_category, axis=1)

    # Define colors and legend labels
    colors = ['green', 'orange', 'red']
    target_info = TARGETS_2030[selected_indicator]
    
    # Define legend labels based on indicator logic
    if target_info['value'] is not None:
        legend_labels = [f"🟢 Target Met (≤ {target_info['value']})" if target_info['goal'] == 'lower_is_better' else f"🟢 Target Met (≥ {target_info['value']})", "🟠 Improving Trend", "🔴 Worsening Trend"]
    elif selected_indicator == 'Real_GDP_Per_Capita':
        legend_labels = ["🟢 High Growth (>10%)", "🟠 Medium Growth (5-10%)", "🔴 Stagnation (<5%)"]
    else:
        legend_labels = ["🟢 Good Trend", "🟠 Neutral", "🔴 Bad Trend"]
        # For 2-state indicators, show only relevant legends
        if df_2030['Category'].nunique() < 3:
            legend_labels = [legend_labels[0], legend_labels[2]] # Keep "🟢 Good Trend" and "🔴 Bad Trend"
            colors = ['green', 'red']

    # Map creation with a single trace
    fig = go.Figure(go.Choropleth(
        locations=df_2030['Country'],
        locationmode='country names',
        z=df_2030['Category'], # Use category for color
        colorscale=[[0, 'green'], [0.5, 'orange'], [1, 'red']], # Fixed palette
        zmin=0, zmax=2,
        showscale=False, # Hide default color bar
        marker_line_color='white',
        marker_line_width=0.2,
        customdata=df_2030[['Country', 'Forecast_Value']],
        hovertemplate='<b>%{customdata[0]}</b><br>%{customdata[1]:.2f}<extra></extra>'
    ))

    fig.update_layout(
        title_text=f"2030 Forecasts for: {selected_indicator.replace('_', ' ')}",
        title_x=0.5,
        template="plotly_white",
        geo=dict(
            scope='europe',
            showframe=False,
            showcoastlines=True,
            landcolor='rgb(230, 230, 230)',
            lataxis_range=[36, 70], # Vertical zoom
            lonaxis_range=[-25, 45], # Horizontal zoom
            projection_type='mercator'
        ),
        margin={"r":0,"t":40,"l":0,"b":0}, # No unnecessary margins
        paper_bgcolor='rgba(0,0,0,0)', # Make the chart background transparent
    )
    return fig

@app.callback(
    Output('map-legend', 'children'),
    Input('map-indicator-dropdown', 'value')
)
def update_legend(selected_indicator):
    """Updates the HTML legend below the map."""
    if not selected_indicator:
        return []

    target_info = TARGETS_2030[selected_indicator]

    if target_info['value'] is not None:
        text_labels = [f"Target Met (≤ {target_info['value']})" if target_info['goal'] == 'lower_is_better' else f"Target Met (≥ {target_info['value']})", "Improving Trend", "Worsening Trend"]
        colors = ['green', 'orange', 'red']
    elif selected_indicator == 'Real_GDP_Per_Capita':
        text_labels = ["High Growth (>10%)", "Medium Growth (5-10%)", "Low Growth (<5%)"]
        colors = ['green', 'orange', 'red']
    else: # 2-state cases
        text_labels = ["Good Trend", "Bad Trend"]
        colors = ['green', 'red']

    # Function to create a color square
    def create_color_square(color):
        return html.Span(style={
            'display': 'inline-block',
            'width': '14px',
            'height': '14px',
            'backgroundColor': color,
            'marginRight': '6px',
            'verticalAlign': 'middle'
        })

    # Create an HTML component for each legend item with a color square
    legend_items = [
        html.Span([create_color_square(colors[i]), html.Span(label, style={'verticalAlign': 'middle'})],
                  style={'marginRight': '20px', 'display': 'inline-block'}) for i, label in enumerate(text_labels)
    ]
    return [html.B("2030 Performance Status: "), *legend_items]

@app.callback(
    Output('country-dropdown', 'value'),
    Input('europe-map', 'clickData'),
    prevent_initial_call=True
)
def update_dropdown_from_map(clickData):
    """Updates the dropdown menu when a country is clicked on the map."""
    if clickData is None:
        # Do nothing if no click has occurred
        from dash import no_update
        return no_update
    
    # Extract the country name from the click data
    country_name = clickData['points'][0]['location']
    return country_name

@app.callback(
    Output('indicator-graphs', 'figure'),
    [Input('country-dropdown', 'value'),
     Input('europe-map', 'clickData'),
     Input('map-indicator-dropdown', 'value')]
)
def update_graphs(selected_country_from_dropdown, map_click_data, selected_indicator):
    """
    Updates the trend graph for the selected country and indicator.
    """
    from dash import callback_context

    # Determine which input triggered the callback
    ctx = callback_context
    if not ctx.triggered:
        selected_country = selected_country_from_dropdown
    else:
        trigger_id = ctx.triggered_id.split('.')[0]
        if trigger_id == 'europe-map' and map_click_data:
            selected_country = map_click_data['points'][0]['location']
        else:
            selected_country = selected_country_from_dropdown

    # If no country or indicator is selected, return an empty figure.
    if not selected_country or not selected_indicator:
        return go.Figure(layout={"title": "Please select a country"})

    # Filter the DataFrame for the selected country and indicator
    filtered_df = df[(df['Country'] == selected_country) & (df['Indicator'] == selected_indicator)]

    # If the filtered dataframe is empty, return an empty figure.
    if filtered_df.empty:
        return go.Figure(layout={"title": f"No data available for {selected_indicator} in {selected_country}"})

    # Find the last year with historical data to mark the forecast start
    last_historical_year = filtered_df.dropna(subset=['Actual_Value'])['Year'].max()

    # Calculate Y-axis range with a 10% margin to avoid cutting off the curve
    min_val = min(filtered_df['Actual_Value'].min(), filtered_df['Forecast_Value'].min())
    max_val = max(filtered_df['Actual_Value'].max(), filtered_df['Forecast_Value'].max())

    # Ensure the target value is included in the range so the red line is visible
    target_info = TARGETS_2030.get(selected_indicator)
    if target_info and target_info['value'] is not None:
        min_val = min(min_val, target_info['value'])
        max_val = max(max_val, target_info['value'])

    padding = (max_val - min_val) * 0.2

    # Create a simple figure
    fig = go.Figure()

    # Add traces for historical data and forecasts
    fig.add_trace(go.Scatter(x=filtered_df['Year'], y=filtered_df['Actual_Value'], mode='markers', name='Historical'))
    fig.add_trace(go.Scatter(x=filtered_df['Year'], y=filtered_df['Forecast_Value'], mode='lines', name='Trend & Forecast'))

    # Add vertical line to mark the start of the forecast
    if pd.notna(last_historical_year):
        fig.add_vline(x=last_historical_year + 0.5, line_width=2, line_dash="dash", line_color="grey",
                      annotation_text="Forecast Start",
                      annotation_position="top left",
                      annotation_font_size=10,
                      annotation_font_color="grey")

    # Add target line if defined
    target_info = TARGETS_2030.get(selected_indicator)
    if target_info and target_info['value'] is not None:
        target_val = target_info['value']
        fig.add_hline(
            y=target_val, 
            line_dash="dot", 
            line_color="red", 
            line_width=2,
            annotation_text=f"Target 2030: {target_val}",
            annotation_position="top right",
            annotation_font_color="red"
        )

    # Update the graph layout
    indicator_title = selected_indicator.replace('_', ' ')
    fig.update_layout(
        title_text=f"Trend for '{indicator_title}' in {selected_country}",
        title_x=0.5,
        xaxis=dict(
            title="Year",
            dtick=5  # Show every 5 years
        ),
        yaxis=dict(
            title="Value",
            range=[min_val - padding, max_val + padding] # Apply calculated range
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.01,
            xanchor="center",
            x=0.5
        ),
        template="plotly_white"
    )

    return fig

# 5. APP LAUNCH 

if __name__ == '__main__':
    app.run(debug=True)
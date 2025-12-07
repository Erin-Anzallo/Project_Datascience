import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import os
import dash_bootstrap_components as dbc

# --- 1. CONFIGURATION ET CHARGEMENT DES DONNÉES ---

# Configuration des chemins
script_dir = os.path.dirname(os.path.abspath(__file__))
# Nous supposons que le dossier 'results' est dans le même répertoire que ce script.
# Le répertoire du script est donc la racine du projet.
project_root = script_dir
data_path = os.path.join(project_root, "results", "forecast_2030", "graph_forecast_data.csv")

# Chargement des données
try:
    df = pd.read_csv(data_path)
    print("Graph data loaded successfully.")
except FileNotFoundError:
    print(f"Error: 'graph_forecast_data.csv' file not found at: {data_path}")
    print("Please run the 'forecast_to_2030.py' script first to generate this file.")
    exit()

# Liste des pays et des indicateurs
countries = df['Country'].unique()
indicators = df['Indicator'].unique()

# Créer des options groupées pour les menus déroulants par ODD
# On filtre pour ne garder que les indicateurs réellement présents dans les données
indicator_groups = {
    "SDG 8: Decent Work and Economic Growth": [ind for ind in ['Real_GDP_Per_Capita', 'Unemployment_Rate', 'NEET_Rate'] if ind in indicators],
    "SDG 10: Reduced Inequalities": [ind for ind in ['Income_Distribution_Ratio', 'Income_Share_Bottom_40'] if ind in indicators],
    "SDG 13: Climate Action": [ind for ind in ['GHG_Emissions', 'Renewable_Energy_Share'] if ind in indicators]
}

# --- 2. INITIALISATION DE L'APPLICATION DASH ---

app = Dash(__name__, external_stylesheets=[dbc.themes.MINTY])
app.title = "Socio-Economic Forecasts 2030"

# --- 3. DÉFINITION DE LA MISE EN PAGE (LAYOUT) ---

app.layout = dbc.Container(fluid=True, className="p-4", children=[
    # Titre principal
    html.H1(
        children='Socio-Economic Forecasts Dashboard for 2030',
        className="text-center mb-4 text-primary"
    ),

    # Description des ODD
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

    # --- Section principale avec Carte et Graphique côte à côte ---
    dbc.Row([
        # Colonne de gauche pour la carte
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
                dcc.Graph(
                    id='europe-map',
                    style={'height': '65vh'},
                    config={'scrollZoom': False, 'displayModeBar': False}
                ),
                html.Div(id='map-legend', className="text-center mt-3"),
            ]), className="h-100")
        ], id='map-column', width=12), # Par défaut, la carte prend toute la largeur

        # Colonne de droite pour le graphique de tendance
        dbc.Col([
            dbc.Card(dbc.CardBody([
                html.H4("Detailed Analysis by Country", className="card-title text-center"),
                html.P("Click a country on the map or select it below.", className="text-center text-muted"),
                dcc.Dropdown(
                    id='country-dropdown',
                    options=[{'label': country, 'value': country} for country in countries],
                    value=countries[0],
                ),
                dcc.Graph(id='indicator-graphs', style={'height': '65vh'}),
            ]), className="h-100")
        ], id='graph-column', width=5, style={'display': 'none'}), # La colonne du graphique est masquée par défaut
    ])
])

# --- 4. DÉFINITION DE L'INTERACTIVITÉ (CALLBACKS) ---

@app.callback(
    [Output('map-column', 'width'),
     Output('graph-column', 'style')],
    [Input('europe-map', 'clickData'),
     Input('map-indicator-dropdown', 'value')]
)
def toggle_graph_view(clickData, selected_indicator):
    """Affiche ou masque le graphique et ajuste la mise en page."""
    # Si aucun indicateur n'est sélectionné, on masque toujours le graphique.
    if selected_indicator is None:
        return 12, {'display': 'none'}
    # Si un indicateur est sélectionné ET qu'un pays a été cliqué, on affiche le graphique.
    if clickData is not None:
        return 7, {'display': 'block', 'height': '100%'}
    # Sinon (indicateur sélectionné mais pas de clic), on garde le graphique masqué.
    return 12, {'display': 'none'}

@app.callback(
    Output('map-indicator-dropdown', 'options'),
    Input('sdg-dropdown', 'value')
)
def set_indicator_options(selected_sdg):
    """Met à jour les options du menu des indicateurs en fonction de l'ODD sélectionné."""
    if not selected_sdg:
        return []
    # Ne proposer que les indicateurs qui existent dans le DataFrame
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
    # If no indicator is selected (on startup), do nothing.
    if selected_indicator is None:
        # Afficher une carte vierge avec une invitation
        fig = go.Figure(go.Scattergeo()) # Initialiser avec une trace géographique vide
        fig.update_layout(
            title_text="Select an SDG and an Indicator to display data",
            title_x=0.5,
            template="plotly_white",
            geo=dict(
                scope='europe',
                showframe=False,
                showcoastlines=True,
                landcolor='rgb(230, 230, 230)',
                lataxis_range=[36, 70], # Zoom vertical
                lonaxis_range=[-25, 45], # Zoom horizontal
                projection_type='mercator'
            ),
            margin={"r":0,"t":40,"l":0,"b":0},
            paper_bgcolor='rgba(0,0,0,0)', # Rendre le fond du graphique transparent
        )
        return fig

    # Filtrer les données pour l'année 2030 et l'indicateur choisi
    df_2030 = df[(df['Year'] == 2030) & (df['Indicator'] == selected_indicator)]

    # --- GESTION D'ERREUR ---
    # Si le dataframe est vide (pas de données pour cet indicateur), retourner une figure vide.
    if df_2030.empty:
        # On ne modifie pas la carte si les données ne sont pas prêtes
        fig = go.Figure()
        fig.update_layout(title_text=f"No forecast data for: {selected_indicator.replace('_', ' ')}", title_x=0.5)
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig

    # --- LOGIQUE DE CLASSIFICATION BASÉE SUR LES RÈGLES MÉTIER ---
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
        # Récupérer la dernière valeur réelle (2022) pour ce pays et cet indicateur
        last_value_series = df[(df['Country'] == row['Country']) & (df['Indicator'] == indicator) & (df['Year'] == 2022)]['Actual_Value']
        if last_value_series.empty:
            return 1 # Orange par défaut si la donnée de 2022 manque
        last_value = last_value_series.iloc[0]

        target_info = targets_2030[indicator]
        
        # Logique pour les indicateurs avec une cible chiffrée
        if target_info['value'] is not None:
            is_met = (target_info['goal'] == 'lower_is_better' and forecast_value <= target_info['value']) or \
                     (target_info['goal'] == 'higher_is_better' and forecast_value >= target_info['value'])
            if is_met:
                return 0 # Vert
            else:
                is_improving = (target_info['goal'] == 'lower_is_better' and forecast_value < last_value) or \
                               (target_info['goal'] == 'higher_is_better' and forecast_value > last_value)
                return 1 if is_improving else 2 # Orange ou Rouge
        
        # Logique pour les indicateurs basés sur la tendance
        else:
            if indicator == 'Real_GDP_Per_Capita':
                growth_pct = ((forecast_value - last_value) / last_value) * 100 if last_value != 0 else 0
                if growth_pct > 10: return 0 # Vert
                elif growth_pct >= 5: return 1 # Orange
                else: return 2 # Rouge
            else: # Autres indicateurs de tendance
                is_good_trend = (target_info['goal'] == 'lower_is_better' and forecast_value < last_value) or \
                                (target_info['goal'] == 'higher_is_better' and forecast_value > last_value)
                return 0 if is_good_trend else 2 # Vert ou Rouge (pas d'Orange pour ces cas)

    df_2030['Category'] = df_2030.apply(get_status_category, axis=1)

    # Définir les couleurs et les étiquettes de légende
    colors = ['green', 'orange', 'red']
    target_info = targets_2030[selected_indicator]
    
    # Définir les étiquettes de légende en fonction de la logique de l'indicateur
    if target_info['value'] is not None:
        legend_labels = [f"🟢 Target Met (≤ {target_info['value']})" if target_info['goal'] == 'lower_is_better' else f"🟢 Target Met (≥ {target_info['value']})", "🟠 Improving Trend", "🔴 Worsening Trend"]
    elif selected_indicator == 'Real_GDP_Per_Capita':
        legend_labels = ["🟢 High Growth (>10%)", "🟠 Medium Growth (5-10%)", "🔴 Stagnation (<5%)"]
    else:
        legend_labels = ["🟢 Good Trend", "🟠 Neutral", "🔴 Bad Trend"]
        # Pour les indicateurs à 2 états, on ne montrera que les légendes pertinentes
        if df_2030['Category'].nunique() < 3:
            legend_labels = [legend_labels[0], legend_labels[2]] # Garde "🟢 Good Trend" et "🔴 Bad Trend"
            colors = [colors[0], colors[2]]

    # Création de la carte avec une seule trace
    fig = go.Figure(go.Choropleth(
        locations=df_2030['Country'],
        locationmode='country names',
        z=df_2030['Category'], # On utilise la catégorie pour la couleur
        colorscale=[[0, 'green'], [0.5, 'orange'], [1, 'red']], # Palette fixe
        zmin=0, zmax=2,
        showscale=False, # On masque la barre de couleur par défaut
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
            lataxis_range=[36, 70], # Zoom vertical
            lonaxis_range=[-25, 45], # Zoom horizontal
            projection_type='mercator'
        ),
        margin={"r":0,"t":40,"l":0,"b":0}, # Pas de marges inutiles
        paper_bgcolor='rgba(0,0,0,0)', # Rendre le fond du graphique transparent
    )
    return fig

@app.callback(
    Output('map-legend', 'children'),
    Input('map-indicator-dropdown', 'value')
)
def update_legend(selected_indicator):
    """Met à jour la légende HTML sous la carte."""
    if not selected_indicator:
        return []

    targets_2030 = {
        'Real_GDP_Per_Capita': {'value': None, 'goal': 'higher_is_better'},
        'NEET_Rate': {'value': 9.0, 'goal': 'lower_is_better'},
        'Unemployment_Rate': {'value': 5.0, 'goal': 'lower_is_better'},
        'Income_Distribution_Ratio': {'value': None, 'goal': 'lower_is_better'},
        'Income_Share_Bottom_40': {'value': None, 'goal': 'higher_is_better'},
        'Renewable_Energy_Share': {'value': 42.5, 'goal': 'higher_is_better'},
        'GHG_Emissions': {'value': None, 'goal': 'lower_is_better'}
    }
    target_info = targets_2030[selected_indicator]

    if target_info['value'] is not None:
        text_labels = [f"Target Met (≤ {target_info['value']})" if target_info['goal'] == 'lower_is_better' else f"Target Met (≥ {target_info['value']})", "Improving Trend", "Worsening Trend"]
        colors = ['green', 'orange', 'red']
    elif selected_indicator == 'Real_GDP_Per_Capita':
        text_labels = ["High Growth (>10%)", "Medium Growth (5-10%)", "Low Growth (<5%)"]
        colors = ['green', 'orange', 'red']
    else: # Cas à 2 états
        text_labels = ["Good Trend", "Bad Trend"]
        colors = ['green', 'red']

    # Fonction pour créer un carré de couleur
    def create_color_square(color):
        return html.Span(style={
            'display': 'inline-block',
            'width': '14px',
            'height': '14px',
            'backgroundColor': color,
            'marginRight': '6px',
            'verticalAlign': 'middle'
        })

    # Créer un composant HTML pour chaque élément de la légende avec un carré de couleur
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

    # Create a simple figure
    fig = go.Figure()

    # Add traces for historical data and forecasts
    fig.add_trace(go.Scatter(x=filtered_df['Year'], y=filtered_df['Actual_Value'], mode='markers', name='Historical'))
    fig.add_trace(go.Scatter(x=filtered_df['Year'], y=filtered_df['Forecast_Value'], mode='lines', name='Trend & Forecast'))

    # Update the graph layout
    indicator_title = selected_indicator.replace('_', ' ')
    fig.update_layout(
        title_text=f"Trend for '{indicator_title}' in {selected_country}",
        title_x=0.5,
        xaxis=dict(
            title="Year",
            dtick=5  # Afficher une graduation tous les 5 ans
        ),
        yaxis_title="Value",
        legend_title="Legend",
        template="plotly_white"
    )

    return fig

# --- 5. LANCEMENT DE L'APPLICATION ---

if __name__ == '__main__':
    app.run(debug=True)
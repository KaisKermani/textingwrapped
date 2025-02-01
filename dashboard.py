from io_utils import msg2df
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.io as pio
import plotly.graph_objects as go
from single_plots import weekday_histogram, hourly_histogram

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SOLAR], suppress_callback_exceptions=True)

# Customizing the plotly template
custom_colors = {
    'background': '#073642',
    'plot_background': '#839496',
    'text': '#ffffff',
    'plot_colors': ['#63BBA2', '#81310E', '#E2D5A1', '#0E6A81', '#BCBACE'],  # Example color for plots
}
# Create a custom template
pio.templates["solar_custom"] = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=custom_colors['background'],
        plot_bgcolor=custom_colors['plot_background'],
        font=dict(color=custom_colors['text']),
    ),
    layout_colorway=custom_colors['plot_colors']
)
# Set the custom template as default
pio.templates.default = "solar_custom"

# Load the data
msg_df = msg2df()

def filter_dataframe(df, start_date, end_date, platforms, pathname):
    df = df[
        (df['datetime'] >= start_date) & (df['datetime'] <= end_date) & (df['platform'].isin(platforms))]
    if pathname == '/dms' or pathname == '/':
        return df[df['chat_type'] == 'dm']
    elif pathname == '/groups':
        return df[df['chat_type'] == 'group']
    elif pathname == '/specific-dm':
        return df[df['chat_name'] == 'Specific DM']

@app.callback(
    Output('weekday_histogram', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname')]
)
def update_weekday_histogram(start_date, end_date, platforms, pathname):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname)

    fig = weekday_histogram(filtered_df)
    return fig

@app.callback(
    Output('hourly_histogram', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname')]
)
def update_hourlyy_histogram(start_date, end_date, platforms, pathname):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname)

    fig = hourly_histogram(filtered_df)
    return fig

# Define the layout for the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Define the callback to update the page content based on the URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    # if pathname == '/dms' or pathname == '/':
        return dbc.Container([
            dbc.NavbarSimple(
                children=[
                    dbc.NavItem(dbc.NavLink("DMs", href="/dms")),
                    dbc.NavItem(dbc.NavLink("Groups", href="/groups")),
                    dbc.NavItem(dbc.NavLink("Specific DM", href="/specific-dm"))
                ],
                brand="Texting Wrapped",
                color="light",
            ),
            dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H5("Filters"),
                            dcc.DatePickerRange(
                                id='date_picker',
                                start_date=msg_df['datetime'].min().date(),
                                end_date=msg_df['datetime'].max().date(),
                            ),
                            dbc.Checklist(
                                options=[
                                    {"label": "WhatsApp", "value": "whatsapp"},
                                    {"label": "Telegram", "value": "telegram"}
                                ],
                                value=["whatsapp", "telegram"],
                                id="platform_checklist",
                                inline=True
                            )
                        ])
                    )
                ], width=12)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="weekday_histogram")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="hourly_histogram")
                ], width=6),
            ])
        ], fluid=True, style={"padding-left": "0"})

if __name__ == '__main__':
    app.run_server(debug=True)
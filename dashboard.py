from io_utils import msg2df
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.io as pio
import plotly.graph_objects as go
from single_plots import (weekday_histogram, hourly_lineplot, messages_per_platform_histogram, response_time_distplot,
                          message_count_distplot, top_10_message_count, word_count_sent_received)
import datetime as dt
import pandas as pd

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
unique_chats = msg_df[['chat_name', 'platform', 'chat_id', 'chat_type']].drop_duplicates().dropna()
unique_chats['display_name'] = unique_chats['chat_name'] + ' - ' + unique_chats['platform']
unique_chats = pd.concat([
    unique_chats[unique_chats['display_name'].str[0].str.isalpha()].sort_values(by='display_name'),
    unique_chats[~unique_chats['display_name'].str[0].str.isalpha()].sort_values(by='display_name')
])

def filter_dataframe(df, start_date, end_date, platforms, pathname, chat_id):
    df = df[
        (df['datetime'] >= start_date) & (df['datetime'] <= end_date) & (df['platform'].isin(platforms))]
    df = df[df['chat_id'] == chat_id] if chat_id else df
    if pathname == '/dms' or pathname == '/':
        return df[df['chat_type'] == 'dm']
    elif pathname == '/groups':
        return df[df['chat_type'] == 'group']

@app.callback(
    Output('weekday_histogram', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_weekday_histogram(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = weekday_histogram(filtered_df)
    return fig

@app.callback(
    Output('hourly_lineplot', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_hourlyy_histogram(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = hourly_lineplot(filtered_df)
    return fig

@app.callback(
    Output('message_count_distplot', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_message_count_distplot(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = message_count_distplot(filtered_df)
    return fig

# Define the layout for the app
app.layout = (html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
]))

@app.callback(
    Output('top_10_message_count', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_top_10_message_count(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = top_10_message_count(filtered_df)
    return fig

# Define the layout for the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('messages_per_platform_histogram', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_messages_per_platform_histogram(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = messages_per_platform_histogram(filtered_df)
    return fig

# Define the layout for the app
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(
    Output('word_count_sent_received_histogram', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_word_count_sent_received(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = word_count_sent_received(filtered_df)
    return fig

@app.callback(
    Output('response_time_distplot', 'figure'),
    [Input('date_picker', 'start_date'),
     Input('date_picker', 'end_date'),
     Input('platform_checklist', 'value'),
     Input('url', 'pathname'),
     Input('chat_dropdown', 'value')
    ]
)
def update_response_time_distplot(start_date, end_date, platforms, pathname, chat_id):
    filtered_df = filter_dataframe(msg_df, start_date, end_date, platforms, pathname, chat_id)

    fig = response_time_distplot(filtered_df)
    return fig

# Define the callback to update the page content based on the URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/dms' or pathname == '/':
        chat_list = unique_chats[unique_chats['chat_type'] == 'dm']
    else:
        chat_list = unique_chats[unique_chats['chat_type'] == 'group']

    chat_list = [{'label': "ALL chats", 'value': False}] + [{'label': row['display_name'], 'value': row['chat_id']}
                                                     for _, row in chat_list.iterrows()]
    return dbc.Container([
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("DMs", href="/dms")),
                dbc.NavItem(dbc.NavLink("Groups", href="/groups")),
                # TODO: Add a new page for facts
                dbc.NavItem(dbc.NavLink("Facts 💅🏻", href="/facts"))
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
                            # start_date=msg_df['datetime'].min().date(),
                            start_date=dt.date(2024, 1, 1),
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
                        ),
                        dcc.Dropdown(
                            id='chat_dropdown',
                            options=chat_list,
                            placeholder="Select a chat",
                            multi=False
                        )
                    ])
                )
            ], width=12)
        ]),
        dbc.Row([
            dbc.Col([
                html.H3("Messaging timeline"),
            ], width=12),
            dbc.Col([
                dcc.Graph(id="weekday_histogram")
            ], width=6),
            dbc.Col([
                dcc.Graph(id="hourly_lineplot")
            ], width=6),
        ]),
        dbc.Row([
            dbc.Col([
                html.H3("Amount of messages"),
            ], width=12),
            # dbc.Col([
            #     dcc.Graph(id="message_count_distplot")
            # ], width=3),
            dbc.Col([
                dcc.Graph(id="top_10_message_count")
            ], width=4),
            dbc.Col([
                dcc.Graph(id="messages_per_platform_histogram")
            ], width=4),
            dbc.Col([
                dcc.Graph(id="word_count_sent_received_histogram")
            ], width=4),
        ]),dbc.Row([
            dbc.Col([
                html.H3("Response rates"),
            ], width=12),
            dbc.Col([
                dcc.Graph(id="response_time_distplot")
            ], width=6),
            # dbc.Col([
            #     dcc.Graph(id="messages_per_platform_histogram")
            # ], width=6),
        ])
    ], fluid=True, style={"padding-left": "0"})

if __name__ == '__main__':
    app.run_server(debug=True)
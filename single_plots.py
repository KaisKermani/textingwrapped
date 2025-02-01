from io_utils import msg2df
import pandas as pd
import plotly.express as px
from datetime import datetime as dt
import plotly.io as pio
import plotly.graph_objects as go


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

def weekday_histogram(msg_df):
    # Determine if messages are sent or received
    msg_df['sent'] = msg_df['person_name'].str.lower().eq('kais')
    msg_df['received'] = ~msg_df['sent']

    # Group by day_of_the_week and platform, and count sent and received messages
    weekday_msg = msg_df.groupby(['day_of_the_week', 'platform']).agg(
        sent=('sent', 'sum'),
        received=('received', 'sum')
    ).reset_index()

    # Melt the dataframe to have a long format suitable for Plotly
    weekday_msg_melted = weekday_msg.melt(id_vars=['day_of_the_week', 'platform'],
                                          value_vars=['sent', 'received'],
                                          var_name='message_type',
                                          value_name='count')

    # Create the histogram with ordered days of the week
    fig = px.histogram(weekday_msg_melted, x='day_of_the_week', y='count', color='message_type',
                       category_orders={
                           'day_of_the_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
                                               'Sunday']},
                       barmode='group', title='Messages Sent and Received per Day of the Week')
    fig.update_layout(xaxis_title="Day of The Week", yaxis_title="Total Message")
    return fig

def hourly_histogram(msg_df):
    # Determine if messages are sent or received
    msg_df['sent'] = msg_df['person_name'].str.lower().eq('kais')
    msg_df['received'] = ~msg_df['sent']

    # Extract the hour from the datetime
    msg_df['hour'] = msg_df['datetime'].dt.hour

    # Group by hour and platform, and count sent and received messages
    hourly_msg = msg_df.groupby(['hour', 'platform']).agg(
        sent=('sent', 'sum'),
        received=('received', 'sum')
    ).reset_index()

    # Melt the dataframe to have a long format suitable for Plotly
    hourly_msg_melted = hourly_msg.melt(id_vars=['hour', 'platform'],
                                        value_vars=['sent', 'received'],
                                        var_name='message_type',
                                        value_name='count')

    # Create the histogram with ordered hours of the day
    fig = px.histogram(hourly_msg_melted, x='hour', y='count', color='message_type',
                       category_orders={'hour': list(range(24))}, nbins=24,
                       barmode='group', title='Messages Sent and Received per Hour of the Day')
    fig.update_layout(xaxis_title="Hour of The Day", yaxis_title="Total Messages")

    return fig

if __name__ == '__main__':
    msg_df = msg2df()
    # Filter only chats of type 'dm' and messages from the year 2025
    msg_df = msg_df[(msg_df['chat_type'] == 'dm') & (msg_df['datetime'].dt.year == 2024)]

    fig = hourly_histogram(msg_df)
    fig.show()
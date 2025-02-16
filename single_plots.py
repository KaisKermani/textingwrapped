from io_utils import msg2df
import pandas as pd
import plotly.express as px
from datetime import datetime as dt
import plotly.io as pio
import plotly.graph_objects as go
import plotly.figure_factory as ff
from scipy.ndimage import gaussian_filter1d


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


def hourly_lineplot(msg_df):
    # Extract the hour from the datetime
    msg_df['hour'] = msg_df['datetime'].dt.hour

    # Group by hour and platform, and count sent and received messages
    hourly_msg = msg_df.groupby(['hour']).agg(
        sent=('sent', 'sum'),
        received=('received', 'sum')
    ).reset_index()

    # Apply Gaussian smoothing
    hourly_msg['sent'] = gaussian_filter1d(hourly_msg['sent'], sigma=0.5)
    hourly_msg['received'] = gaussian_filter1d(hourly_msg['received'], sigma=0.5)

    # Create the line plot
    fig = px.line(hourly_msg, x='hour', y=['sent', 'received'],
                  labels={'value': 'Messages', 'variable': 'Message Type'},
                  title='Messages Sent and Received per Hour of the Day')
    fig.update_layout(xaxis_title="Hour of The Day", yaxis_title="Total Messages")

    return fig

def response_time_distplot(msg_df):
    # Calculate the 95th percentile of the response_time
    percentile_95 = msg_df['response_time'].dt.total_seconds().quantile(0.01)

    # Filter out the values above the 95th percentile
    msg_df = msg_df[msg_df['response_time'].dt.total_seconds() <= percentile_95]

    # Filter sent and received messages
    sent_response_times = msg_df[msg_df['sent']]['response_time'].dt.total_seconds().dropna().tolist()
    received_response_times = msg_df[msg_df['received']]['response_time'].dt.total_seconds().dropna().tolist()

    # Create the distplot
    fig = ff.create_distplot([sent_response_times, received_response_times], group_labels=['Sent', 'Received'],
                             show_hist=False, colors=custom_colors['plot_colors'][:2])
    fig.update_layout(title='Distribution of Response Time for Sent and Received Messages', xaxis_title='Response Time (seconds)', yaxis_title='Density')

    return fig

def message_count_distplot(msg_df, min_messages=20, n_bins=50):
    # Group by chat_name and count the number of messages in each chat
    chat_message_counts = msg_df.groupby(['platform', 'chat_name']).size().reset_index(name='message_count')

    # Filter out the chats with less than min_messages
    valid_chats = chat_message_counts[chat_message_counts['message_count'] >= min_messages]

    # Create the histogram
    fig = px.histogram(valid_chats, x='message_count', nbins=n_bins,
                       title=f'Distribution of Message Counts per Chat (at least {min_messages} messages)',
                       labels={'message_count': 'Number of Messages'},
                       color_discrete_sequence=custom_colors['plot_colors'][:1])
    fig.update_layout(xaxis_title="Number of Messages", yaxis_title="Count of Chats")

    return fig


def top_10_message_count(msg_df):
    # Group by chat_name and count the number of messages in each chat
    chat_message_counts = msg_df.groupby(['platform', 'chat_name']).size().reset_index(name='message_count')
    top_10_chats = chat_message_counts.nlargest(10, 'message_count')

    # Ensure unique chat_name by appending platform if there are duplicates
    duplicates = top_10_chats['chat_name'].duplicated(keep=False)
    top_10_chats.loc[duplicates, 'chat_name'] = top_10_chats.loc[duplicates].apply(
        lambda row: f"{row['chat_name']} ({row['platform']})", axis=1
    )

    # Create the bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_10_chats['chat_name'],
        y=top_10_chats['message_count'],
        customdata=top_10_chats['platform'],
        text=top_10_chats['message_count'],
        hovertemplate='Platform: %{customdata}',
    ))

    fig.update_layout(
        title='Message Counts',
        xaxis_title='Chat Name',
        yaxis_title='# Messages',
    )
    return fig


def messages_per_platform_histogram(msg_df):
    # Group by platform and count sent and received messages
    platform_msg = msg_df.groupby(['platform']).agg(
        sent=('sent', 'sum'),
        received=('received', 'sum')
    ).reset_index()

    # Melt the dataframe to have a long format suitable for Plotly
    platform_msg_melted = platform_msg.melt(id_vars=['platform'],
                                            value_vars=['sent', 'received'],
                                            var_name='message_type',
                                            value_name='count')

    # Create the histogram
    fig = px.histogram(platform_msg_melted, x='platform', y='count', color='message_type',
                       barmode='group', title='Messages Sent and Received per Platform')
    fig.update_layout(xaxis_title="Platform", yaxis_title="Total Messages")
    return fig


def word_count_sent_received(msg_df):
    # Add a column to indicate message type
    msg_df['message_type'] = msg_df['sent'].apply(lambda x: 'sent' if x else 'received')

    # Group by platform and message type, and calculate total word count and number of messages
    platform_msg = msg_df.groupby(['platform', 'message_type']).agg(
        total_word_count=('word_count', 'sum'),
        message_count=('word_count', 'count')
    ).reset_index()

    # Calculate the average word count
    platform_msg['average_word_count'] = platform_msg['total_word_count'] / platform_msg['message_count']

    # Create the bar chart with ordered colors
    fig = px.bar(platform_msg, x='platform', y='average_word_count', color='message_type',
                 barmode='group', title='Average Word Count per Message Type and Platform',
                 category_orders={'message_type': ['sent', 'received']})  # Example colors
    fig.update_layout(xaxis_title="Platform", yaxis_title="Average Word Count")
    return fig


def response_time_distplot(msg_df):
    # Define the bins and labels
    bins = [0, 10, 60, 300, 1200, 3600, 18000, 43200, 172800, 604800, 2592000, 7776000, 15768000, 31536000, 94608000]
    labels = ['0-10secs', '10-60secs', '1-5mins', '5-20mins', '20mins-1hr', '1-5hrs', '5-12hrs', '12hrs-2days',
              '2days-1week', '1week-1month', '1month-3months', '3-6months', '6months-1year', '1year-3years']

    # Create a new column for the binned response times
    msg_df['response_time_bins'] = pd.cut(msg_df['response_time'].dt.total_seconds(), bins=bins, labels=labels, right=False)

    # Map the boolean 'sent' column to 'Sent' and 'Received'
    msg_df['sent'] = msg_df['sent'].map({True: 'Sent', False: 'Received'})

    # Create the histogram
    fig = px.histogram(
        msg_df,
        x='response_time_bins',
        color='sent',
        title='Distribution of Response Time for Sent and Received Messages',
        category_orders={'response_time_bins': labels, 'sent': ['Sent', 'Received']},
        barmode='group'  # Set barmode to 'group' to place bins next to each other
    )
    fig.update_layout(
        xaxis_title='Response Time',
        yaxis_title='Count'
    )

    return fig

if __name__ == '__main__':
    msg_df = msg2df()
    # Filter only chats of type 'dm' and messages from the year 2025
    msg_df = msg_df[(msg_df['chat_type'] == 'dm') & (msg_df['datetime'].dt.year == 2024)]

    unique_chats = msg_df[['chat_name', 'platform', 'chat_id']].drop_duplicates().dropna()
    unique_chats['display_name'] = unique_chats['chat_name'] + ' - ' + unique_chats['platform']
    unique_chats = pd.concat([
        unique_chats[unique_chats['display_name'].str[0].str.isalpha()].sort_values(by='display_name'),
        unique_chats[~unique_chats['display_name'].str[0].str.isalpha()].sort_values(by='display_name')
    ])

    # msg_df = msg_df[msg_df['chat_id'] == 308786296]
    fig = response_time_distplot(msg_df)
    fig.show()
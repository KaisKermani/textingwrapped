import logging
import sys
from io_utils import msg2df
import pandas as pd
import plotly.express as px


logger = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# TODO: switch to dash for the full dashboard
def main():
    msg_df = msg2df()

    # Filter only chats of type 'dm' and messages from the year 2025
    msg_df = msg_df[(msg_df['chat_type'] == 'dm') & (msg_df['datetime'].dt.year == 2025)]

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

    fig.show()


if __name__ == '__main__':
    main()
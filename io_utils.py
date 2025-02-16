import pandas as pd
import zipfile
import os
import re
from datetime import datetime as dt
import json

# TODO: add links as type of messages

def whatsapp2df(folder_path):
    data = []
    weird_chars = ['\u202a', '\u202c', '\xa0', '\u200e', '\u202f']
    chat_id_counter = 0
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.zip') and file_name.startswith('WhatsApp Chat - '):
            chat_name = file_name[16:-4]
            chat_id_counter += 1
            with zipfile.ZipFile(os.path.join(folder_path, file_name), 'r') as zip_ref:
                for inner_file in zip_ref.namelist():
                    if inner_file.endswith('_chat.txt'):
                        with zip_ref.open(inner_file) as f:
                            content = f.read().decode('utf-8')
                            content = content.translate(str.maketrans('', '', ''.join(weird_chars)))
                            messages = content.split('\r\n')
                            for line in messages:
                                if "Messages and calls are end-to-end encrypted. No one outside of this chat" in line:
                                    continue
                                match = re.match(r'\[(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2}:\d{2})\] (.*?): (.*)', line)
                                if match:
                                    date_str, time_str, person_name, msg_content = match.groups()
                                    datetime_str = f"{date_str} {time_str}"
                                    datetime_obj = dt.strptime(datetime_str, '%d.%m.%y %H:%M:%S')
                                    day_of_the_week = datetime_obj.strftime('%A')

                                    if msg_content == "audio omitted":
                                        msg_type = "audio"
                                    elif msg_content == "image omitted":
                                        msg_type = "image"
                                    elif msg_content == "video omitted":
                                        msg_type = "video"
                                    else:
                                        msg_type = "text"

                                    word_count = len(msg_content.split())
                                    data.append([datetime_obj, day_of_the_week, chat_name, chat_id_counter, person_name, msg_type, msg_content, word_count])

    df = pd.DataFrame(data, columns=['datetime', 'day_of_the_week', 'chat_name', 'chat_id', 'person_name', 'msg_type', 'msg_content', 'word_count'])
    df.insert(2, 'platform', 'whatsapp')
    chats_participant_count = df.groupby('chat_name')['person_name'].nunique()
    df['chat_type'] = df['chat_name'].apply(lambda x: 'group' if chats_participant_count[x] > 2 else 'dm')
    df.insert(4, 'chat_type', df.pop('chat_type'))
    return df

def telegram2df(json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        chats = json.load(file)['chats']['list']

    data = []
    for chat in chats:
        chat_name = chat['name']
        chat_id = chat['id']
        chat_type = 'group' if chat['type'] in ['private_group', 'private_supergroup'] else 'dm'
        for message in chat['messages']:
            if message['type'] == 'message':
                datetime_obj = dt.fromisoformat(message['date'])
                day_of_the_week = datetime_obj.strftime('%A')
                person_name = message['from']
                person_id = message['from_id']
                msg_content, has_link = extract_text(message['text'])
                msg_type = message.get('mime_type', 'text')

                word_count = len(msg_content.split())
                data.append([datetime_obj, day_of_the_week, chat_name, chat_id, chat_type, person_name, person_id, msg_type, has_link, msg_content, word_count])

    df = pd.DataFrame(data, columns=['datetime', 'day_of_the_week', 'chat_name', 'chat_id', 'chat_type', 'person_name', 'person_id', 'msg_type', 'has_link', 'msg_content', 'word_count'])
    df.insert(2, 'platform', 'telegram')
    return df


def extract_text(text):
    has_link = False
    if isinstance(text, list):
        full_text = ''
        for item in text:
            if isinstance(item, dict) and item.get('type') == 'link':
                has_link = True
            full_text += item['text'] if isinstance(item, dict) else item
        return full_text, has_link
    return text, has_link


def msg2df(telegram_file = 'data/telegram.json', whatsapp_folder = 'data/whatsapp'):
    whatsapp_df = whatsapp2df(whatsapp_folder)
    telegram_df = telegram2df(telegram_file)

    # Concatenate the DataFrames, keeping all columns
    combined_df = pd.concat([telegram_df, whatsapp_df], ignore_index=True, sort=False)
    combined_df = combined_df[telegram_df.columns]

    # Add response time column
    combined_df = combined_df.sort_values(by=['chat_name', 'datetime'])

    # Add sent and received columns
    combined_df['sent'] = combined_df['person_name'].str.lower().eq('kais')
    combined_df['received'] = ~combined_df['sent']

    # Group by chat_name and calculate the response time
    combined_df['previous_datetime'] = combined_df.groupby('chat_id')['datetime'].shift(1)
    combined_df['response_time'] = combined_df['datetime'] - combined_df['previous_datetime']

    # Drop the temporary column
    combined_df = combined_df.drop(columns=['previous_datetime'])

    return combined_df


if __name__ == '__main__':
    df = telegram2df('data/telegram.json')
    print(df.head())
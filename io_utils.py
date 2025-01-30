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
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.zip') and file_name.startswith('WhatsApp Chat - '):
            chat_name = file_name[16:-4]
            with zipfile.ZipFile(os.path.join(folder_path, file_name), 'r') as zip_ref:
                for inner_file in zip_ref.namelist():
                    if inner_file.endswith('_chat.txt'):
                        with zip_ref.open(inner_file) as f:
                            content = f.read().decode('utf-8')
                            content = content.translate(str.maketrans('', '', ''.join(weird_chars)))
                            messages = content.split('\r\n')
                            for line in messages:
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

                                    data.append([datetime_obj, day_of_the_week, chat_name, person_name, msg_type, msg_content])

    df = pd.DataFrame(data, columns=['datetime', 'day_of_the_week', 'chat_name', 'person_name', 'msg_type', 'msg_content'])
    df.insert(2, 'platform', 'whatsapp')
    chats_participant_count = df.groupby('chat_name')['person_name'].nunique()
    df['chat_type'] = df['chat_name'].apply(lambda x: 'group' if chats_participant_count[x] > 2 else 'dm')
    df.insert(4, 'chat_type', df.pop('chat_type'))
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


def telegram2df(json_path):
    with open(json_path, 'r', encoding='utf-8') as file:
        chats = json.load(file)['chats']['list']

    data = []
    for chat in chats:
        chat_name = chat['name']
        chat_id = chat['id']
        chat_type = 'group' if chat['type'] == 'private_group' else 'dm'
        for message in chat['messages']:
            if message['type'] == 'message':
                datetime_obj = dt.fromisoformat(message['date'])
                day_of_the_week = datetime_obj.strftime('%A')
                person_name = message['from']
                person_id = message['from_id']
                msg_content, has_link = extract_text(message['text'])
                msg_type = message.get('mime_type', 'text')

                data.append([datetime_obj, day_of_the_week, chat_name, chat_id, chat_type, person_name, person_id, msg_type, has_link, msg_content])

    df = pd.DataFrame(data,
                      columns=['datetime', 'day_of_the_week', 'chat_name', 'chat_id', 'chat_type', 'person_name', 'person_id', 'msg_type', 'has_link',
                               'msg_content'])
    df.insert(2, 'platform', 'telegram')
    return df


def msg2df():
    whatsapp_df = whatsapp2df('data/whatsapp')
    telegram_df = telegram2df('data/telegram.json')

    # Concatenate the DataFrames, keeping all columns
    combined_df = pd.concat([telegram_df, whatsapp_df], ignore_index=True, sort=False)
    combined_df = combined_df[telegram_df.columns]

    return combined_df


if __name__ == '__main__':
    df = telegram2df('data/telegram.json')
    print(df.head())
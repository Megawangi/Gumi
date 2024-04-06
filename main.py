import requests
import os, base64, json, logging, re, random
from datetime import datetime

from colorama import init, Fore, Style
init()

with open('config.json') as config_file:
    config_data = json.load(config_file)
    password = config_data['password'] 
    webhook = config_data.get('webhook', '')

for _ in range(5): # Retry 5x you can change it!
    user_password = input(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Enter password: ")

    if base64.b64encode(user_password.encode('utf-8')).decode('utf-8') == password:
        break
    else:
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Incorrect password. Please try again... {Fore.GREEN}[Default Password is 'OZMoon']{Style.RESET_ALL}")

else:
    print(f"{Fore.RED}[SHUTDOWN]{Style.RESET_ALL} Incorrect password 5x times! Shutdown the program...")
    exit()

logpath = 'log/logs.json'
if not os.path.exists(logpath):
    with open(logpath, 'w') as log_file:
        log_file.write('[]')

logging.basicConfig(filename=logpath, level=logging.INFO)

def decode_protobuf_message(data):
    message = {}
    offset = 0
    while offset < len(data):
        field_header = data[offset]
        field_number = field_header >> 3
        wire_type = field_header & 0b111
        offset += 1
        if wire_type == 0:
            varint = 0
            shift = 0
            byte = 0
            while byte & 0b10000000:
                byte = data[offset]
                varint |= (byte & 0b01111111) << shift
                offset += 1
                shift += 7
            if field_number == 1:
                message['retcode'] = varint
        elif wire_type == 2:
            length = data[offset]
            offset += 1
            value = data[offset:offset + length]
            offset += length
            if field_number == 2:
                message['msg'] = value.decode('utf-8')
        elif wire_type == 3:
            repeated_length = data[offset]
            offset += 1
            repeated_value = data[offset:offset + repeated_length]
            offset += repeated_length
            if 'regionList' not in message:
                message['regionList'] = []
            message['regionList'].append(repeated_value.decode('utf-8'))
    return message

def extract_urls(text):
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return urls

def send_to_discord_webhook(log_entry, webhook):
    if not webhook:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Discord webhook URL is not provided.")
        return

    headers = {
        'Content-Type': 'application/json'
    }

    embed_color = random.randint(0, 0xFFFFFF)

    if log_entry['urls']:
        embed_color = 0x00FF00
    else:
        embed_color = 0xFF0000

    ownerName = config_data["owner"]
    mention = "@here" if log_entry['urls'] else f"@everyone Hey **{ownerName}**"

    embed = {
        'title': f"{mention} {log_entry['version']} Version check:",
        'fields': [
            {'name': 'Response Status Code', 'value': str(log_entry['response_status_code']), 'inline': True},
            {'name': 'Raw Decoded Content', 'value': str(log_entry['raw_dec_content']), 'inline': False},
            {'name': 'Decoded Message', 'value': str(log_entry['dec_message']), 'inline': False},
            {'name': 'URLs', 'value': '\n'.join(log_entry['urls']), 'inline': False}
        ],
        'color': embed_color,
        'footer': {
            'text': 'Timestamp: ' + str(datetime.now())
        }
    }

    payload = {
        'embeds': [embed]
    }

    response = requests.post(webhook, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL}Failed to send log to Discord webhook.")
    else:
        print(f"{Fore.GREEN}[SEND]{Style.RESET_ALL}Log sent successfully to Discord webhook.")




while True:
    version = input(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Write Star Rail Version (use number ex: '1.3.51') or ('exit' 'quit' 'stop' 'shutdown') to stop the program: ")

    byee = {'exit', 'quit', 'stop', 'shutdown'}
    if version.lower() in byee:
        print(f"{Fore.RED}[STOP]{Style.RESET_ALL} Shutdown the program...")
        break

    encoded_url = config_data["url"]
    deurl = base64.b64decode(encoded_url).decode('utf-8')
    url = f'{deurl}{version}&language_type=3&platform_type=1&channel_id=1&sub_channel_id=1&is_new_format=1'

    response = requests.get(url)

    print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Status Code: {response.status_code}")

    try:
        dec_data = base64.b64decode(response.content)
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Raw Message Content for Version {version}: {dec_data}")

        dec_message = decode_protobuf_message(dec_data)
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Result Message for Version {version}: {dec_message}")
        
        urls = extract_urls(str(dec_data))
        if urls:
            print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} Check Message contains URL:")
            for url in urls:
                print(url)
                
        log_entry = {
            'version': version,
            'response_status_code': response.status_code,
            'raw_dec_content': str(dec_data),
            'dec_message': dec_message,
            'urls': urls
        }

        send_to_discord_webhook(log_entry, webhook)

        with open(logpath, 'r') as log_file:
            logs = json.load(log_file)
        logs.append(log_entry)
        with open(logpath, 'w') as log_file:
            json.dump(logs, log_file, indent=2)

    except Exception as e:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} message: {e}")

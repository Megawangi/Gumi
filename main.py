import re
import requests
import base64
import json
import logging
import os

# Default Password: OZMoon
password = 'T1pNb29u' # Feel free to change it use base64 encoder ! 

for _ in range(3):
    user_password = input("Enter password: ")

    if base64.b64encode(user_password.encode('utf-8')).decode('utf-8') == password:
        break
    else:
        print("Incorrect password. Please try again.")

else:
    print("Incorrect password. Exiting the program...")
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

while True:
    version = input("Write Star Rail Version (use number ex: '1.3.51') or ('exit' 'quit' 'stop' 'shutdown') to stop the program: ")

    byee = {'exit', 'quit', 'stop', 'shutdown'}
    if version.lower() in byee:
        print("Exiting the program...")
        break

    url = f'' # Add Dispatch Url Here

    response = requests.get(url)

    print(f"Response Status Code: {response.status_code}")

    try:
        dec_data = base64.b64decode(response.content)
        print(f"Raw Message Content for Version {version}: {dec_data}")

        dec_message = decode_protobuf_message(dec_data)
        print(f"Result Message for Version {version}: {dec_message}")

        urls = extract_urls(str(dec_data))
        if urls:
            print("Check Message contains URL(s):")
            for url in urls:
                print(url)
                
        log_entry = {
            'version': version,
            'response_status_code': response.status_code,
            'raw_dec_content': str(dec_data),
            'dec_message': dec_message,
            'urls': urls
        }
        with open(logpath, 'r') as log_file:
            logs = json.load(log_file)
        logs.append(log_entry)
        with open(logpath, 'w') as log_file:
            json.dump(logs, log_file, indent=2)
    except Exception as e:
        print(f"Error message: {e}")
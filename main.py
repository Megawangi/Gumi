import requests
import base64

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

while True:
    version = input("Write Star Rail Version or('exit' to stop): ")

    if version.lower() == 'exit':
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

    except Exception as e:
        print(f"Error message: {e}")
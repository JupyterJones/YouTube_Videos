import base64

def encode_audio(data):
    return base64.b64encode(data).decode('utf-8')

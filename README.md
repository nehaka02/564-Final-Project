# 564-Final-Project

## TODO

- **C2 Server (Attacking Machine)**
  - Hosts a script that defines API endpoints
  - Endpoints can be invoked by either the client (implant) or the controller

- **Implant Obfuscation Strategy**
  - ~~Uses a **dummy GET** request followed by **POST** requests to request tasks~~
  - Using tradition client/server model between C2 Server and implant 

- **Team Responsibilities**
  - **Neha**  
    - Implements controller logic to queue tasks and upload endpoint
    - Explores steganography techniques
  - **Saadhvi**  
    - Implements dummy GET and POST behavior in the client  
    - Focuses on hiding web traffic
  - **Varun**  
    - Handles self-destruction logic for client  
    - Applies XOR obfuscation to the implant

## FUTURE

- Implement **AES encryption**

## 4/29 Notes 
- **Implementation Details**
  - Implant Obfuscation : XOR the binary
  - C2 Security:
    - Encryption: Encrypt commands that C2 sends to the implant
  - Exfiltration Security:
    - Encrypting the output of the given command
    - Obfuscating using steganography 



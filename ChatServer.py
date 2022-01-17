import sys
import socket
import threading
import os

ChatClients = []

def recv_msg(sock, username):
    msg = sock.recv(1024)
    while msg:
        msg = msg.decode()
        bmsg = "{}: {}".format(username, msg)
        broadcast(bmsg, username)
        msg = sock.recv(1024)
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    for client in ChatClients:
        if client[0] == username:
            ChatClients.remove(client)
    sys.exit()

def broadcast(msg, sender):
    for client in ChatClients:
        if client[0] != sender:
            clientsock = client[1]
            try:
                clientsock.send(msg.encode())
            except:
                client.close()
                ChatClients.remove(client) 

def ManageFileRequests(sock):
    while True:
        found = False
        username = sock.recv(1024)
        username = username.decode()
        for client in ChatClients:
            if client[0] == username:
                found = True
                sock.send(client[2].encode())
        if found == False:
            try:
                sock.send("false".encode())
            except:
                pass
        
                

if __name__ == "__main__":
    port = int(sys.argv[1])
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind(('', port))
    serversocket.listen(10)
    while True:
        port = port + 1
        RequestSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        RequestSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        RequestSocket.bind(('', port))
        RequestSocket.listen(1)
        clientsocket, addr = serversocket.accept()
        username = clientsocket.recv(1024)
        username = username.decode()
        clientsocket.send(str(port).encode())
        fileport = clientsocket.recv(1024)
        fileport = fileport.decode()
        MiddleSocket, addr = RequestSocket.accept()
        RequestSocket.close()
        ChatClients.append((username,clientsocket,fileport))
        RequestThrd = threading.Thread(target=ManageFileRequests, args=(MiddleSocket,))
        RequestThrd.start()
        RecvThrd = threading.Thread(target=recv_msg, args=(clientsocket,username,))
        RecvThrd.start()

    clientsocket.close()
    serversocket.close()
    os._exit(0)

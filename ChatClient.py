import sys
import socket
import threading
import os
import getopt
import struct

def recv_msg(sock):
    msg = sock.recv(1024)
    while msg:
        print(msg.decode(), end='')
        msg = sock.recv(1024)
    sock.shutdown(socket.SHUT_RD)
    sock.close()
    os._exit(0)

def no_file( sock ):
    zero_bytes= struct.pack( '!L', 0 )
    sock.send( zero_bytes )
    
def send_file( sock, file_size, file ):
    file_size_bytes= struct.pack( '!L', file_size )
    sock.send( file_size_bytes )
    while True:
        file_bytes= file.read(1024)
        if file_bytes:
            sock.send( file_bytes )
        else:
            #print("done Sending")
            break
    file.close()
 
    
def receive_file( sock, filename ):
    #print("receiving file")
    file= open( filename, 'wb' )
    while True:
        #print("getting bytes")
        file_bytes= sock.recv(1024)
        if file_bytes:
            file.write( file_bytes )
        else:
            #print("done writing")
            break
    file.close()
    

def CheckFile(SendSock, filename):
    try:
        file_stat = os.stat(filename)
        if file_stat.st_size:
            file = open(filename, 'rb')
            send_file(SendSock, file_stat.st_size, file)
        else:
            no_file(SendSock)
    except:
        no_file(SendSock)
    SendSock.shutdown(socket.SHUT_RDWR)
    SendSock.close() 
    
def fileServer(serversocket):
    while True:
        serversocket.listen(5) 
        ClientSock, addr = serversocket.accept()
        filename = ClientSock.recv(1024)
        filename = filename.decode()
        TransferThread = threading.Thread(target=CheckFile, args=(ClientSock,filename))
        TransferThread.start()
    
def MakeRequest(rSock, filename, ownername):
    rSock.send(ownername.encode())
    port = rSock.recv(1024)
    port = port.decode()

    if port != "false":
        ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ServerSocket.connect(('', int(port)))
        ServerSocket.send(filename.encode())
        file_size_bytes= ServerSocket.recv(4)
        if file_size_bytes:
	        file_size= struct.unpack( '!L', file_size_bytes[:4] )[0]
	        if file_size:
		        receive_file(ServerSocket, filename)
	        else:
	    	    print('File does not exist or is empty')
        else:
            print('File does not exist or is empty')
        ServerSocket.shutdown(socket.SHUT_RDWR)
        ServerSocket.close()
    
def MenuOptions(mSock, rSock):
    while True:
        print("Enter an option ('m', 'f', 'x'):\n  (M)essage (send)\n  (F)ile (request)\n e(X)it")
        choice = sys.stdin.readline().rstrip('\n')
        if choice == 'm':
            print("Enter your message:")
            msg = sys.stdin.readline()
            mSock.send(msg.encode())
        if choice == 'f':
            print("Who owns the file?")
            ownername = sys.stdin.readline().rstrip( '\n' )
            print("Which file do you want?")
            filename = sys.stdin.readline().rstrip( '\n' )
            fileRequestThread = threading.Thread(target=MakeRequest, args=(rSock, filename, ownername))
            fileRequestThread.start()
        if choice == 'x':
            print("closing your sockets...goodbye")
            break        

if __name__ == "__main__":
    hostname = 'localhost'
    ListenPort = None
    ServerPort = None

    opts, args = getopt.getopt(sys.argv[1:], 'l:p:')
    for opt, arg in opts:
        if opt in ['-l']:
            ListenPort = arg
        if opt in ['-p']:
            ServerPort = arg

    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Waiting for request from server...")
    clientsocket.connect(('localhost', int(ServerPort)))
    #Send Username
    name = input("What is your name?\n")
    print("Sending name to server...")
    clientsocket.send(name.encode())
    #Recieve port to connect
    ConnectPort = clientsocket.recv(1024)
    ConnectPort = ConnectPort.decode()
    #send Port to receive files
    clientsocket.send(ListenPort.encode())
    #Connect to port to find fileport from server
    RequestSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    RequestSocket.connect(("localhost", int(ConnectPort)))
    #Start recieve message thread
    RecvThrd = threading.Thread(target=recv_msg, args=(clientsocket,))
    RecvThrd.start()
    #Create the Socket to listen for File Requests
    ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ServerSocket.bind(('', int(ListenPort)))
    #Launch FileServer to listen for file requests 
    FileServerThrd = threading.Thread(target=fileServer, args=(ServerSocket,))
    FileServerThrd.start()
    #Start the main menu options
    MenuOptions(clientsocket, RequestSocket)
        
    clientsocket.shutdown(socket.SHUT_WR)
    clientsocket.close()
    os._exit(0)

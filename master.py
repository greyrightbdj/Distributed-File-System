import glob
import os
import pickle
import socket
import subprocess
import sys
import time
from image_slicer import chunk_image
from image_slicer import combine_image
import threading
from PIL import Image

s_names = list()
s_ports = list()
client_status = list()
subprocesses = list() 
clients = [
    ('127.0.0.1','10001'),
    ('127.0.0.1','10002'),
    ('127.0.0.1','10003'),
    # ('127.0.0.1','10004'),
    # ('127.0.0.1','10005'),
    # ('127.0.0.1','10006'),
    # ('127.0.0.1','10007'),
]
num_clients = len(clients)

def start_client(ip,port):
    try:
        p = subprocess.Popen('start python dfs_client.py '+ip+" "+port, shell=True)
        subprocesses.append(p)
        print("Client at port: "+port+" started.")
    except:
        print("Error starting the client at port: "+port)

client_sockets = list()
def client():
    global client_status
    global client_sockets
    for client in clients:
        start_client(client[0],client[1])
    
    for client in clients:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((client[0],int(client[1])))
            client_sockets.append(client_socket)
            print("Connected to server at Host:"+client[0]+" and Port:"+client[1])
            client_status.append("Connected")
            time.sleep(1)
        except ConnectionRefusedError:
            client_sockets.append(None)
            client_status.append("Failed")
            print("Failed to connect at Host:"+client[0]+" and Port:"+client[1])

client()

if len([1 for x in client_status if x == 'Connected']) == 0:
    print("No Active Client.\nExiting.")
    time.sleep(2)
    sys.exit()

def get_filename():
        images = []
        print('Current files: ')
        print('-' * 15)
        for file in glob.glob("*.jpg"):
            images.append(file)
            print(file.split(".")[0])
        print('\n')
        filename = input('Please specify a file: ')
        # check if file exists
        try:
            statinfo = os.stat(filename + '.jpg')
            return (filename , statinfo)
        except FileNotFoundError:
            print('There is no such file in the directory.\nPlease try again.\n')

def get_recieve_filename():
    filename = input('Please specify a file: ')
    return filename

def get_command():
    comm = input('Please specify a command [get, put, exit]: ')
    if comm in ("get", "list", "put", "exit"):
        return comm
    return get_command()

def send_command(cmd,client_socket,idx):
    try:
        client_socket.send((cmd+" "+str(idx)).encode())
    except OSError:
        pass

def send_file_name(client_socket,filename):
    try:
        client_socket.send(filename.encode())
    except OSError:
        pass

def send_data(filename_statinfo,chunk,client_socket):
    try:
        HEADERSIZE = 10
        FILENAME_HEADER = 50
        filename = filename_statinfo[0]
        chunk = pickle.dumps(chunk)
        chunk = bytes(f"{len(chunk):<{HEADERSIZE}}", 'utf-8')+bytes(f"{filename:<{FILENAME_HEADER}}", 'utf-8')+chunk
        client_socket.send(chunk)
    except OSError:
        pass

def recieve_data(idx,client_socket):
    HEADERSIZE = 10
    print("Waiting for Client",str(idx),sep= ' ')
    success_msg = client_socket.recv(256)
    try:
        if pickle.loads(success_msg[HEADERSIZE:]) == "Recieved File.":
            print(f"File Recieved at {idx}")
    except Exception as e:
        print(e)

recieved_chunks = {}
def recieve_file(idx,client_socket):
    global recieved_chunks
    full_chunk =b''
    new_msg = True
    HEADERSIZE = 10
    FILENAME_HEADER = 50
    recieved = False
    print('Recieving from Client ',str(idx))
    try:
        while not recieved:
            chunk = client_socket.recv(1024)
            if new_msg:
                chunk_len = int(chunk[:HEADERSIZE])
                #print("Length of chunk is : "+str(chunk_len))
                new_msg = False
                
            full_chunk+=chunk
            if len(full_chunk)-(HEADERSIZE) == chunk_len:
                try:
                    full_chunk = pickle.loads(full_chunk[HEADERSIZE:])
                    recieved = True
                except Exception as e:
                    print(e)
        chunk = 'Recieved file from Client' +str(idx)
        print(chunk)
        chunk = pickle.dumps(chunk)
        recieved_chunks[idx] = full_chunk
    except:
        pass


done = False
while not done:
    cmd = get_command()
    if cmd == 'exit':
        send_command_threads = []
        for idx,client_socket in enumerate(client_sockets):    
            thread = threading.Thread(target=send_command, args=(cmd,client_socket,idx))
            thread.start()
            send_command_threads.append(thread)
        for thread in send_command_threads:
            thread.join()
        done = True
    elif cmd == 'put':
        #threads
        send_command_threads = []
        for idx,client_socket in enumerate(client_sockets):    
            thread = threading.Thread(target=send_command, args=(cmd,client_socket,idx))
            thread.start()
            send_command_threads.append(thread)
        
        for thread in send_command_threads:
            thread.join()
        
        filename_statinfo = get_filename()
        chunks = chunk_image(filename_statinfo[0]+".jpg",num_clients)

        send_data_threads = []
        for idx,client_socket,chunk in zip(range(0,len(client_sockets)),client_sockets,chunks):
            thread = threading.Thread(target=send_data, args=(filename_statinfo,chunk,client_socket))
            thread.start()
            send_data_threads.append(thread)
            
        for thread in send_data_threads:
            thread.join()

        rcv_data_threads = []
        for idx,client_socket,chunk in zip(range(0,len(client_sockets)),client_sockets,chunks):
            thread = threading.Thread(target=recieve_data, args=(idx,client_socket))
            thread.start()
            rcv_data_threads.append(thread)
            
        for thread in rcv_data_threads:
            thread.join()
        print("File Saved Successfully.")

    elif cmd == 'get':
        send_command_threads = []
        for idx,client_socket in enumerate(client_sockets):    
            thread = threading.Thread(target=send_command, args=(cmd,client_socket,idx))
            thread.start()
            send_command_threads.append(thread)
            thread.join()

        filename = get_recieve_filename()

        
        for idx,client_socket in zip(range(0,len(client_sockets)),client_sockets):
            thread = threading.Thread(target=send_file_name, args=(client_socket,filename))
            thread.start()
            thread.join()
        recieve_file_threads = []
        for idx,client_socket in zip(range(0,len(client_sockets)),client_sockets):
            thread = threading.Thread(target=recieve_file, args=(idx,client_socket))
            thread.start()
            recieve_file_threads.append(thread)
        for thread in recieve_file_threads:
            thread.join()
        
        final_image = combine_image([recieved_chunks[x] for x in sorted(recieved_chunks)])
        data = Image.fromarray(final_image)
        try:
            os.makedirs("Recieved")
        except:
            pass
        os.chdir('./Recieved')
        data.save(filename+'.jpg')
        os.chdir('..')
        print("File retrieved successfully")



import os
import pickle
import socket
import sys
import time
from PIL import Image
import numpy

# function to check port number assignment
def check_args():
	if len(sys.argv) != 3:
		print("ERROR: Must supply port number \nUSAGE: py dfs1.py 10001")

check_args()

# RUN DFS -------------------------------------------------	
server_name = sys.argv[1]
server_port = int(sys.argv[2])

# define socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((server_name, server_port))
server_socket.listen(5)
print('Server listening...')

def get_directory(client_number):
	curr_directory = os.getcwd()
	try:
		os.makedirs("Client_"+str(client_number))
	except:
		pass
	return os.path.join(curr_directory, "Client_"+str(client_number))
try:
	conn, client_address = server_socket.accept()
	while True:
		print('Connected to Client and Listening...')
		command = conn.recv(1024).decode()
		client_number = int(command.split(" ")[1])+1
		command = command.split(" ")[0]
		if  command == 'exit':
			sys.exit()
		elif command == 'put':
			print("Put Command Recieved.")
			full_chunk =b''
			new_msg = True
			HEADERSIZE = 10
			FILENAME_HEADER = 50
			recieved = False
			print('Recieving File.')
			try:
				while not recieved:
					chunk = conn.recv(1024)
					if new_msg:
						chunk_len = int(chunk[:HEADERSIZE])
						chunk_name = str(chunk[HEADERSIZE:FILENAME_HEADER].decode("utf-8")).strip()
						new_msg = False						
					full_chunk+=chunk
					if len(full_chunk)-(HEADERSIZE+FILENAME_HEADER) == chunk_len:
						try:
							full_chunk = pickle.loads(full_chunk[HEADERSIZE+FILENAME_HEADER:])
							recieved = True
						except Exception as e:
							print(e)
				
				chunk = 'Recieved File.'
				print(chunk)
				chunk = pickle.dumps(chunk)
				chunk = bytes(f"{len(chunk):<{HEADERSIZE}}", 'utf-8')+chunk
				conn.send(chunk)
				directory = get_directory(client_number=client_number)
				data = Image.fromarray(full_chunk)
				data.save(os.path.join(directory,chunk_name+"_"+str(client_number)+'.jpg'))
				print("Chunk saved successfully at client ",str(client_number) )		
			except Exception as e:
				print(e)
		elif command == 'get':
			print("Get Command Recieved.")
			directory = get_directory(client_number=client_number)
			filename = conn.recv(1024).decode() 
			filename = filename + "_" + str(client_number)
			try:
				img= Image.open(os.path.join(directory,filename + ".jpg"))
				np_img = numpy.array(img)
				print("File found.\nNow sending.")
			except Exception as e:
				print(e)
				print("File Not found.")
			try:
				HEADERSIZE = 10
				chunk = pickle.dumps(np_img)
				chunk = bytes(f"{len(chunk):<{HEADERSIZE}}", 'utf-8')+chunk
				conn.send(chunk)
			except OSError:
				print("Error Sending File: ",e)
except Exception as e:
	print("Error: ",e)
	time.sleep(10)        

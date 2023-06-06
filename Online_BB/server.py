import sys
from socket import *
import os
import json
from datetime import datetime

# Check the boards initially here before starting the server
# Ensure the folder board exists
if not os.path.isdir("./board"):
    print("You don't have a folder called board.")
    sys.exit()
# Ensure that the folder board has at least one subfolder
if not os.listdir("./board"):
    print("You have no boards defined.")
    sys.exit()
# Loop over all the boards in the folder and rename them to have underscores of needed
directories = os.listdir("./board")
for subdirectory in directories:
    if " " in subdirectory:
        new_name = subdirectory.replace(" ", "_")
        os.rename(("./board/" + subdirectory), ("./board/" + new_name))

# IP is the first argument passed, this should be a string
serverIP = str(sys.argv[1])
# Port is the second argument passed, this should be an integer
serverPort = int(sys.argv[2])
serverSocket = socket(AF_INET, SOCK_STREAM)
try:
    # Try to bind the socket
    serverSocket.bind((serverIP, serverPort))
except IOError as e:
    # Print the error and quit of the socket is in use or if there is any other error
    print(e)
    sys.exit()
serverSocket.listen(1)
print("The server is ready to receive!\nPlease startup the client(s).")


def log(type_message, success):
    global serverIP
    global serverPort
    today = datetime.now()
    # Get the date in the format needed for the log
    formatted_date = today.strftime("%Y%m%d-%H%M%S")
    f = open("server.log", "a+")
    f.write(
        str(serverIP)
        + ":"
        + str(serverPort)
        + "\t"
        + formatted_date
        + "\t"
        + type_message
        + "\t"
        + success
        + "\n"
    )
    f.close()


# A function to list all the message boards
def get_boards():
    try:
        boards = sorted(os.listdir("./board"))
        message = {"boards": boards, "error": "none"}
        message = json.dumps(message)
    except:
        message = {"error": sys.exc_info()[1]}
        log("GET_BOARDS", "Error")
        return json.dumps(message)
    else:
        log("GET_BOARDS", "OK")
        return message


def get_messages(board):
    try:
        # List all the messages in the given board
        messages = sorted(os.listdir("./board/" + board))
        response = {"error": "none", "messages": {}}
        # For file in first 100 messages
        for file in messages[:100]:
            # Get the contents of the file
            f = open("./board/" + board + "/" + file)
            contents = f.read()
            # Change the filename to not include the date
            title = file.split("-", 2)[-1]
            # Remove the underscores from the title and replace with spaces
            title = title.replace("_", " ")
            # Add the message and contents to the response
            response["messages"][title] = contents
        response = json.dumps(response)
    except:
        message = {"error": sys.exc_info()[1]}
        log("GET_MESSAGES", "Error")
        return json.dumps(message)
    else:
        log("GET_MESSAGES", "OK")
        return response


def post_message(board, title, content):
    try:
        today = datetime.now()
        # Get the date in the format needed for the title
        formatted_date = today.strftime("%Y%m%d-%H%M%S")
        # Change the title to use underscores rather than spaces
        title = title.replace(" ", "_")
        # Get all the boards
        boards = sorted(os.listdir("./board"))
        # Get the string of the selected board
        selected_board = boards[int(board) - 1]
        # Create the file with the correct title
        f = open("./board/" + selected_board + "/" + formatted_date + "-" + title, "w")
        # Write the content to the file
        f.write(content)
        f.close()
    except:
        message = {"error": sys.exc_info()[1]}
        log("POST_MESSAGE", "Error")
        return json.dumps(message)
    else:
        log("POST_MESSAGE", "OK")
        response = {"error": "none"}
        return json.dumps(response)


while True:
    connectionSocket, addr = serverSocket.accept()
    # The client shouldn't send anything over 1024 bytes,
    # so anything over this will be handled as an error
    sentence = connectionSocket.recv(1024).decode()
    try:
        sentence = json.loads(sentence)
    except json.decoder.JSONDecodeError:
        print("The server did not receive valid JSON.")
    else:
        if sentence["command"] == "GET_BOARDS":
            connectionSocket.send(get_boards().encode())
        if sentence["command"] == "POST_MESSAGE":
            connectionSocket.send(
                post_message(
                    sentence["board"], sentence["title"], sentence["content"]
                ).encode()
            )
        if sentence["command"] == "GET_MESSAGES":
            connectionSocket.send(get_messages(sentence["board"]).encode())
        if sentence["command"] == "QUIT":
            connectionSocket.send(json.dumps({"error": "none"}).encode())
            log("QUIT", "OK")
            sys.exit()
    connectionSocket.close()

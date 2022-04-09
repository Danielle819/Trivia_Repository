import random
import socket
import chatlib
import select

# GLOBALS
users = {}  # username: {password: _, score: _, questions_asked: []}
questions = {}  # id: {question: _, answers: [_,_,_,_], correct: _}
logged_users = {}  # sock.getpeername(): username
messages_to_send = []  # (socket, message)
client_sockets = []  # client_socket

ERROR_MSG = "Error! "
SERVER_PORT = 1984
SERVER_IP = "127.0.0.1"

STR_ANSWERS = {  # possible answers the clients can send
	"one": 1, "One": 1, "ONE": 1,
	"two": 2, "Two": 2, "TWO": 2,
	"three": 3, "Three": 3, "THREE": 3,
	"four": 4, "Four": 4, "FOUR": 4
}


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
	"""
	Builds a new message using chatlib, wanted code and message.
	Prints debug info, then sends it to the given socket.
	Parameters: conn (socket object), code (str), msg (str)
	Returns: Nothing
	"""

	global messages_to_send

	message = chatlib.build_message(code, str(msg))
	messages_to_send.append((conn, message))


def recv_message_and_parse(conn):
	"""
	Receives a new message from given socket.
	Prints debug info, then parses the message using chatlib.
	Parameters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message.
	If error occurred, will return None, None
	"""
	try:
		data = conn.recv(10019).decode()
	except ConnectionResetError:
		return "", ""
	if data == "":
		return "", ""
	cmd, msg = chatlib.parse_message(data)
	return cmd, msg


def print_client_sockets():
	for key in logged_users.keys():
		print(key)


# Data Loaders #

def load_questions():
	"""
	Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: questions dictionary
	"""
	q = {}
	f = open("C:\\Users\\Daniel\\Documents\\PYProject\\Trivia_Game\\questions.txt", "r")
	data = f.read().split("\n")
	q_id = 1
	for line in data:
		question, o1, o2, o3, o4, answer = line.split("|")
		q[q_id] = {"question": question, "answers": [o1, o2, o3, o4], "correct": int(answer)}
		q_id += 1
	f.close()

	return q


def load_user_database():
	"""
	Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
	Receives: -
	Returns: user dictionary
	"""

	u = {}
	f = open("users.txt", "r")
	data = f.read().split("\n")
	for line in data:
		username, password, score, qs = line.split("|")
		u[username] = {"password": password, "score": int(score), "questions_asked": []}
		if qs != '':
			if ',' not in qs:
				u[username]["questions_asked"].append(int(qs))
			else:
				qs = qs.split(",")
				for q in qs:
					u[username]["questions_asked"].append(int(q))
	f.close()

	return u


# SOCKET CREATOR

def setup_socket():
	"""
	Creates new listening socket and returns it
	Receives: -
	Returns: the socket object
	"""

	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((SERVER_IP, SERVER_PORT))
	sock.listen(10)

	return sock


def send_error(conn, error_msg):
	"""
	Send error message with given message
	Receives: socket, message error string from called function
	Returns: None
	"""

	build_and_send_message(conn, "ERROR", error_msg)


# MESSAGE HANDLING


def handle_getscore_message(conn, username):
	global users

	cmd = chatlib.PROTOCOL_SERVER["your_score_msg"]
	msg = users[username]["score"]

	build_and_send_message(conn, cmd, msg)


def handle_gethighscore_message(conn):
	global users

	highscore = ""
	for user in users:
		highscore += user + ": " + str(users[user]["score"]) + "\n"

	build_and_send_message(conn, chatlib.PROTOCOL_SERVER["all_score_msg"], highscore)


def handle_getlogged_message(conn):
	global logged_users

	logged = ""
	for username in logged_users.values():
		logged += username + ", "

	build_and_send_message(conn, chatlib.PROTOCOL_SERVER["logged_answer_msg"], logged[:-2])


def create_random_question(username):
	global users
	global questions

	questions_keys = list(questions)
	random.shuffle(questions_keys)

	questions_asked = users[username]["questions_asked"]
	q_id = None

	if len(questions_asked) == 0:
		q_id = 1
	else:
		for key in questions_keys:
			if key not in questions_asked:
				q_id = key
				break

	if q_id is None:
		return None

	users[username]["questions_asked"].append(q_id)

	question = questions[q_id]
	message = str(q_id) + "#" + question["question"] + "#"

	answers = question["answers"]
	for a in answers:
		message += str(a) + "#"


	return message[:-1]


def handle_question_message(conn, username):
	question_msg = create_random_question(username)

	if question_msg is None:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER["no_question_msg"], "")
		return

	build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_question_msg"], question_msg)


def handle_answer_message(conn, username, answer):
	global users
	global questions

	q_id, choice = answer.split("#")
	try:
		choice = int(choice)
	except ValueError:
		if choice not in STR_ANSWERS:
			q = users[username]["questions_asked"]
			q.remove(q[len(q) - 1])
			send_error(conn, "Invalid answer")
			return
		else:
			choice = STR_ANSWERS[choice]
	else:
		if choice < 1 or choice > 4:
			q = users[username]["questions_asked"]
			q.remove(q[len(q) - 1])
			send_error(conn, "Invalid answer")
			return

	correct_answer = questions[int(q_id)]["correct"]
	if correct_answer == choice:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_answer_msg"], "")
		users[username]["score"] += 5
	else:
		build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_answer_msg"], str(correct_answer))



def handle_logout_message(conn):
	"""
	Closes the given socket (in later chapters, also remove user from logged_users dictionary)
	Receives: socket
	Returns: None
	"""
	global logged_users

	try:
		logged_users.pop(conn.getpeername())
	except KeyError:
		return


def handle_login_message(conn, data):
	"""
	Gets socket and message data of login message. Checks  user and pass exists and match.
	If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
	Recieves: socket, message code and data
	Returns: None (sends answer to client)
	"""
	global users  # This is needed to access the same users dictionary from all functions
	global logged_users  # To be used later

	username, password = data.split("#")

	a_cmd = chatlib.PROTOCOL_SERVER["login_ok_msg"]
	a_msg = ""

	if username not in users:
		send_error(conn, "Unrecognised username")
		return
	elif password != users[username]["password"]:
		send_error(conn, "Incorrect password")
		return

	logged_users[conn.getpeername()] = username
	build_and_send_message(conn, a_cmd, a_msg)


def handle_client_message(conn, cmd, data):
	"""
	Gets message code and data and calls the right function to handle command
	Receives: socket, message code and data
	Returns: None
	"""
	global logged_users  # To be used later

	if conn.getpeername() not in logged_users:
		if cmd == "LOGIN":
			username = data.split("#")[0]
			if username not in logged_users.values():
				handle_login_message(conn, data)
			else:
				send_error(conn, "User already logged in")
			return
		else:
			send_error(conn, "User not connected")
			return

	username = logged_users[conn.getpeername()]

	if cmd == "LOGOUT":
		handle_logout_message(conn)
	elif cmd == "MY_SCORE":
		handle_getscore_message(conn, username)
	elif cmd == "GET_QUESTION":
		handle_question_message(conn, username)
	elif cmd == "SEND_ANSWER":
		handle_answer_message(conn, username, data)
	elif cmd == "LOGGED":
		handle_getlogged_message(conn)
	elif cmd == "HIGHSCORE":
		handle_gethighscore_message(conn)
	else:
		send_error(conn, "Unrecognised command")


def send_waiting_messages(messages, wlist):
	for message in messages:
		current_socket, data = message
		if current_socket in wlist:
			current_socket.send(data.encode())
			messages.remove(message)



def main():
	global users
	global questions
	global messages_to_send
	global client_sockets

	print("Welcome to the Haikyuu Trivia Server!")
	print("Haikyuu is a sport anime and manga about volleyball.")
	print("Enjoy!")

	users = load_user_database()
	questions = load_questions()

	server_socket = setup_socket()

	while True:
		rlist, wlist, xlist = select.select([server_socket] + client_sockets, client_sockets, [])
		for current_socket in rlist:
			if current_socket is server_socket:
				(new_socket, address) = server_socket.accept()
				print("new socket connected to server: ", new_socket.getpeername())
				client_sockets.append(new_socket)
			else:
				cmd, msg = recv_message_and_parse(current_socket)
				if cmd != "":
					handle_client_message(current_socket, cmd, msg)
				else:
					p_id = current_socket.getpeername()
					client_sockets.remove(current_socket)
					handle_logout_message(current_socket)
					print(f"Connection with client {p_id} closed.")
		send_waiting_messages(messages_to_send, wlist)








if __name__ == '__main__':
	main()

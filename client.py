import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 1984


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), msg (str)
    Returns: Nothing
    """

    message = chatlib.build_message(code, msg)
    conn.send(message.encode())


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
        return None, None
    cmd, msg = chatlib.parse_message(data)
    return cmd, msg


def build_send_recv_parse(conn, cmd, data):
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def connect():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, SERVER_PORT))
    return client_socket


def error_and_exit(msg):
    print("error:", msg)
    exit()


def login(conn):
    while True:
        username = input("\nPlease enter username: ")
        password = input("Please enter password: ")

        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], username + "#" + password)
        data = conn.recv(10019).decode()
        cmd, msg = chatlib.parse_message(data)
        if cmd == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print("\n----- LOGIN succeeded -----")
            return
        if cmd == chatlib.PROTOCOL_SERVER["error_msg"]:
            print("\nLOGIN failed")
            print(msg)


def get_score(conn):
    cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["my_score_msg"], "")
    if cmd != "YOUR_SCORE":
        print("\nERROR - score wasn't received")
        print("command:", cmd, "message:", msg)
    else:
        print("\nscore:", msg)


def play_question(conn):
    q_cmd, q_msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    if q_cmd == chatlib.PROTOCOL_SERVER["no_question_msg"]:
        print("\nthere are no more questions!")
        return
    if q_cmd != chatlib.PROTOCOL_SERVER["your_question_msg"]:
        print("\nERROR - a question wasn't received")
        print("command:", q_cmd, "message:", q_msg)
        return

    question = q_msg.split("#")
    print("\n#" + question[0], question[1])
    for i in range(2, len(question)):
        print(f"{i-1}.", question[i])

    answer = input("enter the number of your answer: ")
    answer = question[0] + "#" + answer

    a_cmd, a_msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], answer)

    if a_cmd == chatlib.PROTOCOL_SERVER["correct_answer_msg"]:
        print("\nCORRECT ANSWER! WELL DONE!")
    elif a_cmd == chatlib.PROTOCOL_SERVER["wrong_answer_msg"]:
        print("\nyou were wrong. correct answer: ", a_msg)
    else:
        print("\nan ERROR has occurred.")
        print("command:", a_cmd, "message:", a_msg)


def get_highscore(conn):
    cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["highscore_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["all_score_msg"]:
        print("\n" + msg)
    else:
        print("\nan error has occurred.")
        print("command:", cmd, "message:", msg)


def get_logged_users(conn):
    cmd, msg = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_msg"], "")
    if cmd == chatlib.PROTOCOL_SERVER["logged_answer_msg"]:
        print("\n" + msg)
    else:
        print("\nan error has occurred.")
        print("command:", cmd, "message:", msg)


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")
    print("client LOGOUT")


def main():
    client_socket = connect()
    login(client_socket)

    print("\nWHAT DO YOU WANT TO DO?")
    print("commands: S - get your score, Q - get a question, H - get the scores table")
    print("          U - get all the logged users, L - logout")
    cmd = input("your command: ")
    while cmd != 'L':
        if cmd == "S":
            get_score(client_socket)
        elif cmd == "Q":
            play_question(client_socket)
        elif cmd == "H":
            get_highscore(client_socket)
        elif cmd == "U":
            get_logged_users(client_socket)
        else:
            print("invalid answer. try again.")
        print("\ncommands: S - get your score, Q - get a question, H - get the scores table")
        print("          U - get all the logged users, L - logout")
        cmd = input("WHAT DO YOU WANT TO DO? ")
    logout(client_socket)
    client_socket.close()


if __name__ == '__main__':
    main()

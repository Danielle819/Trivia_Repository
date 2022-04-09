# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol

# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",  # username#password
    "logout_msg": "LOGOUT",  # ''
    "logged_msg": "LOGGED",  # ''
    "get_question_msg": "GET_QUESTION",  # ''
    "send_answer_msg": "SEND_ANSWER",  # id#choice
    "my_score_msg": "MY_SCORE",  # ''
    "highscore_msg": "HIGHSCORE"  # ''
}

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",  # ''
    "login_failed_msg": "ERROR",  # the error
    "logged_answer_msg": "LOGGED_ANSWER",  # username1, username2…
    "your_question_msg": "YOUR_QUESTION",  # id#question#answer1#answer2#answer3#answer4
    "correct_answer_msg": "CORRECT_ANSWER",  # ''
    "wrong_answer_msg": "WRONG_ANSWER",  # correct answer
    "your_score_msg": "YOUR_SCORE",  # score
    "all_score_msg": "ALL_SCORE",  # user1: score1\nnuser2: score2\n...
    "error_msg": "ERROR",  # the error
    "no_question_msg": "NO_QUESTIONS"  # ''
}

# Other constants

CMD_FIELD = CMD_FIELD_LENGTH * ' '
LENGTH_FIELD = LENGTH_FIELD_LENGTH * ' '


def build_message(cmd, data):
    """
    Gets command name and data field and creates a valid protocol message
    Returns: str, or None if error occurred
    """
    if len(cmd) > CMD_FIELD_LENGTH:
        return None

    data_length = len(data)

    if data_length > 9999:
        return None

    command = (cmd + CMD_FIELD)[:CMD_FIELD_LENGTH]
    length = (LENGTH_FIELD + str(data_length))[-LENGTH_FIELD_LENGTH:]

    full_msg = join_msg([command, length, data])

    return full_msg


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occurred, returns None, None
    """

    if data == "" or "|" not in data:
        return None, None

    expected_fields = 3

    splt_msg = split_msg(data, expected_fields)
    command = splt_msg[0]

    if command is None:
        return None, None

    # removing unnecessary spaces from the command
    cmd = ""
    for char in command:
        if char.isalpha() or char == '_':
            cmd += char

    if cmd not in PROTOCOL_CLIENT.values() and cmd not in PROTOCOL_SERVER.values():
        return None, None

    length = splt_msg[1]
    try:
        length = int(length)
    except ValueError:
        return None, None

    msg = splt_msg[2]
    if length != len(msg):
        return None, None

    return cmd, msg


def split_msg(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's delimiter (|) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occurred, returns None
    """

    splitted_msg = msg.split('|')
    if len(splitted_msg) == expected_fields:
        return splitted_msg
    else:
        # creating a list of None in the length of the expected fields
        none_list = []
        for i in range(expected_fields):
            none_list.append(None)
        return none_list


def join_msg(msg_fields):
    """
    Helper method. Gets a list, joins all of its fields to one string divided by the delimiter.
    Returns: string that looks like cell1|cell2|cell3
    """

    msg = ""
    for field in msg_fields:
        msg += str(field) + "|"

    return msg[:-1]

# protocol.py

SEPARATOR = "|"
ID_SEPARATOR = ": "

# Tipos de mensagem
MSG = "MSG"
STATUS = "STATUS"
KEEP_ALIVE = "KEEP_ALIVE"

def create_message(message_type, data):
    return f"{message_type}{SEPARATOR}{data}"

def parse_message(message):
    try:
        # Primeiro, separa o tipo da mensagem e o restante
        message_type, content = message.split(SEPARATOR, 1)
        
        # Depois, tenta separar o ID do cliente e o conteúdo da mensagem
        if ID_SEPARATOR in content:
            client_id, message_content = content.split(ID_SEPARATOR, 1)
            return message_type, [client_id, message_content]
        else:
            return message_type, [content]
    except ValueError:
        return None, []

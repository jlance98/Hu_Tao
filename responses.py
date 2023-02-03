import mangadex


def handle_response(message: str) -> str:
    p_message = message.lower()

    func, *param = p_message.split(" ", 1)

    if func == 'help':
        return 'Help commands coming soon'

    if func == 'search':
        ids = mangadex.search_manga(message, param[0])
        return f'{ids}'

    else:
        return p_message

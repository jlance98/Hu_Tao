import mangadex


def handle_response(message: str) -> str:
    p_message = message.lower()

    func, *param = p_message.split(" ", 1)

    if func == 'help':
        result = 'Help commands coming soon'

    elif func == 'search':
        closest_title, closest_id = mangadex.manga_search(param[0])

        # Format string to return to user
        result = f'Closest matching title: **{closest_title}**\n' \
                 f'Link: https://mangadex.org/title/{closest_id}\n'

    elif func == 'chapter':
        latest_chId, latest_chNum, latest_chTtl = mangadex.manga_latest_chapter(param[0])

        # Format string to return to user
        result = f'Chapter {latest_chNum}, **{latest_chTtl}**\n' \
                 f'https://mangadex.org/chapter/{latest_chId}'

    elif func == 'read':
        title, latest_title, chapter = mangadex.manga_read_chapter(param[0])

        # Format string to return to user
        if title == "N/A":
            result = "The chapter you read is above the latest chapter available on Mangadex."
        else:
            result = f'You read **chapter {chapter}: {latest_title}** of **{title}**'

    elif func == 'check':
        outdated_mangas = mangadex.manga_check_update()

        # Format string to return to user
        result = "Mangas that got an update: \n"
        if len(outdated_mangas) == 0:
            result = "You are up to date!"
        else:
            for manga in outdated_mangas:
                result += f'https://mangadex.org/title/{manga} \n'

    else:
        result = p_message

    return result

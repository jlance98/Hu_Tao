import discord
import pymongo
from discord.ext import commands
import mangadex
from dotenv import load_dotenv
import os

load_dotenv()


def run_discord_bot():
    TOKEN = os.getenv("TOKEN")
    intents = discord.Intents.default()
    intents.message_content = True
    hutao = commands.Bot(command_prefix="!hutao ", intents=intents)

    @hutao.command()
    async def info(ctx):
        result = f'**search "manga_title"**\n' \
                 f'Returns the manga whose title best matches the specified title.\n\n' \
                 f'**latest "manga_title"**\n' \
                 f'Returns the latest chapter of the specified manga\n\n' \
                 f'**read "manga_title" ch_param**\n' \
                 f'Marks the chapter number specified by "ch_param" as read for the specified title.\n' \
                 f'- If "-l" is entered for "ch_param", uses the latest chapter of the manga.\n\n' \
                 f'- If "-r" is entered for "ch_param", manga_title can be a number from !hutao check.\n\n' \
                 f'**check**\n' \
                 f'Checks if the user is caught up with the latest chapter of any of their read mangas.'
        await ctx.send(result)

    @hutao.command()
    async def search(ctx, arg):
        closest_title, closest_id = mangadex.manga_search(arg)
        if closest_title == "N/A":
            result = "No manga could be found with that title in Mangadex."
        else:
            result = f'Closest matching title: **{closest_title}**\n' \
                     f'Link: https://mangadex.org/title/{closest_id}\n'
        await ctx.send(result)

    @hutao.command()
    async def read(ctx, title, read_chapter):
        title, read_chapter = mangadex.manga_read_chapter(title, read_chapter)
        if title == "N/A":
            result = "The chapter you read is either above the latest chapter available on Mangadex " \
                     "or the manga is not available in Mangadex."
        elif title == "RUNUPDATE":
            result = "Run !hutao check first to use -r command."
        elif title == "ALL":
            result = "All mangas have been read up to date."
        else:
            result = f'You read chapter {read_chapter} of **{title}**'
        await ctx.send(result)

    @hutao.command()
    async def latest(ctx, arg):
        latest_chId, latest_chNum, latest_chTtl = mangadex.manga_latest_chapter(arg, False)
        if latest_chId == "N/A":
            result = "No manga could be found with that title in Mangadex."
        else:
            result = f'Chapter {latest_chNum}, **{latest_chTtl}**\n' \
                     f'https://mangadex.org/chapter/{latest_chId}'
        await ctx.send(result)

    @hutao.command()
    async def check(ctx):
        outdated_mangas = mangadex.manga_check_update()
        if len(outdated_mangas) == 0:
            result = "You are up to date!"
        else:
            result = "Mangas that got an update: \n"
            for index, manga in enumerate(outdated_mangas):
                result += f'[{index+1}]: **{manga[1]}**\nhttps://mangadex.org/title/{manga[0]} \n'
                if index % 5 == 0:
                    await ctx.send(result)
                    result = ""

        await ctx.send(result)

    @hutao.command()
    async def remove(ctx, arg):
        removed_title = mangadex.manga_delete_manga(arg)
        if removed_title == "N/A":
            result = "No manga could be found with that title in Mangadex."
        elif removed_title == "DNE":
            result = "Manga was not found in database."
        else:
            result = f'**{removed_title}"** was successfully removed from database.'

        await ctx.send(result)

    hutao.run(TOKEN)


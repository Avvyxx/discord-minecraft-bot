from util import *
from commands import handleCommand

import discord, textwrap, subprocess, sys, requests, json, os
from dotenv import load_dotenv

token_env_name = 'TOKEN'

load_dotenv()

if (token_env_name not in os.environ):
    raise Exception(token_env_name + ' not defined in .env.')

token = os.getenv(token_env_name)

class MyClient(discord.Client):
    async def on_read(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author != self.user:
            # check if message is command
            if (message.content[0] == '/'):
                message_tokens = message.content[1:].split()

                try:
                    await handleCommand(message, message_tokens)
                except Exception as e:
                    # TODO: Ping me, or everyone in admins list
                    print(e)
                    await message.channel.send(f'There seems to have been an error: `{type(e).__name__}: {str(e)}`\nPlease ping an admin.')


client = MyClient()
client.run(token)

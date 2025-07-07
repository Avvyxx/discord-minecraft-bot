admins = ['avvyxx']
server_domain = 'minecraft.avyx.home'
registered_servers = set()

import discord, textwrap, subprocess, sys, requests, json, os
from dotenv import load_dotenv

token_env_name = 'TOKEN'

load_dotenv()

if (token_env_name not in os.environ):
    raise Exception(token_env_name + ' not defined in .env.')

token = os.getenv(token_env_name)

is_locked = False

def getUsername(UserorMember):
    return str(UserorMember).split('#')[0]

def discordInlineCode(s):
    return f'`{s}`'

def isAdmin(UserorMember):
    return getUsername(UserorMember) in admins

def ping_machine():
    result = subprocess.run('ping -c 1 ' + server_domain, shell=True, executable='/bin/bash')

    return result.returncode == 0

def ping_api():
    url = f'http://{server_domain}:8000/ping'
    json_response = json.loads(requests.get(url).text)

    return json_response[0] == 'pong'

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
                    await message.channel.send(f'There seems to have been an error: `{type(e).__name__}: {str(e)}`\nPlease ping an admin.')

async def handleCommand(message, message_tokens):
    if not message_tokens:
        return

    command = message_tokens[0]

    if command in command_reference:
        is_privileged = command_reference[command]['is_privileged']
        is_admin = isAdmin(message.author)

        if is_locked:
            if command == 'release' and is_admin:
                await handleRelease(message, message_tokens)
            else:
                await message.channel.send('Currently not accepting commands.')
        elif (is_privileged and is_admin) or (not is_privileged) or (command == 'release' and is_admin):
            await command_reference[command]['handler'](message, message_tokens)
        else:
            await message.channel.send(f'Who do you think you are, {getUsername(message.author)}.')
    else:
        await message.channel.send('Unkown command: ' + command)

async def handleLock(message, message_tokens):
    global is_locked

    is_locked = True

    await message.channel.send('Commands locked.')

async def handleRelease(message, message_tokens):
    global is_locked

    if is_locked:
        is_locked = False

        await message.channel.send('Lock released.')
    else:
        await message.channel.send('There is no lock.')

# list all for /help
# list specified for /help <command>
async def handleHelp(message, message_tokens):
    if len(message_tokens) == 1:
        message_to_send = textwrap.dedent(command_reference['help']['help']['detailed']) + '\n'

        message_to_send += 'Available commands:\n'

        for command in command_reference:
            message_to_send += f'\\- {discordInlineCode(command)}: {command_reference[command]['help']['blurb']}\n'

        message_to_send += 'Try: `/help list`'

        await message.channel.send(message_to_send)
    elif len(message_tokens) == 2:
        help_command = message_tokens[1]

        if help_command in command_reference:
            help_reference = command_reference[help_command]['help']

            message_to_send = help_reference['blurb'].strip() + '\n'

            message_to_send += '\n' + textwrap.dedent(help_reference['detailed']).strip() + '\n\n' if help_reference['detailed'] else '\n'

            message_to_send += 'Usage: ' + discordInlineCode(help_reference['usage'])

            await message.channel.send(message_to_send)
        else:
            await message.channel.send('Uknown command: ' + help_command)
    else:
        await message.channel.send('Usage: ' + discordInlineCode(command_reference['help']['help']['usage']))

# register servers
# writes to file of registered servers
# for now will write to variable
async def handleRegister(message, message_tokens):
    username = getUsername(message.author)

    if username.lower() in admins:
        if len(message_tokens) < 2:
            await message.channel.send('You must specify at least 1 server.')
        else:
            global registered_servers

            to_register = []
            message_to_send = ''

            for server in message_tokens[1:]:
                if server in registered_servers:
                    message_to_send += f'Server "{server}" is already registered.\n'
                else:
                    to_register.append(server)

            registered_servers.update(to_register)

            if to_register:
                message_to_send += f'Registered: {', '.join(to_register)}.'

            await message.channel.send(message_to_send)
    else:
        await message.channel.send(f'Who do you think you are, {username}')

async def handleActivate(message, message_tokens):
    await message.channel.send('Activating newton.')

    result = subprocess.run('~/wake-newton.sh', shell=True, executable='/bin/bash')

    if result.returncode == 0:
        print('Magic packet successfully sent.')
    else:
        print('Magic packet unsucessfully sent.')
        await message.channel.send('Failed to wake newton.')

# check if newton is responding
# should wait a certain amount of time before deciding newton is not responding
async def handlePing(message, message_tokens):
    tokens_amount = len(message_tokens)

    # TODO: condense this somehow
    if tokens_amount == 1:
        if ping_machine():
            if ping_api():
                await message.channel.send('Both newton and the API are runnning.')
            else:
                await message.channel.send('Newton is running but the API is not running.')
        else:
            await message.channel.send('Newton is not running.')
    elif tokens_amount == 2:
        subcommand = message_tokens[1]

        if subcommand == 'machine':
            message_to_send = 'Newton is running.' if ping_machine() else 'Newton is not running.'

            await message.channel.send(message_to_send)
        elif subcommand == 'api':
            message_to_send = 'API is running.' if ping_api() else 'API is not running.'

            await message.channel.send(message_to_send)
        else:
            await message.channel.send('Usage: ' + discordInlineCode(command_reference['ping']['help']['usage']))
    else:
        await message.channel.send('Usage: ' + discordInlineCode(command_reference['ping']['help']['usage']))


# list with an extra set of commands
# list running
# list available
# list: usage <running | available>
async def handleList(message, message_tokens):
    if len(message_tokens) == 2:
        subcommand = message_tokens[1]

        url = f'http://{server_domain}:8000/list'
        json_response = json.loads(requests.get(url).text)

        if not json_response:
            await message.channel.send('There are no available servers.')
            return

        if subcommand == 'status':
            message_to_send = ''

            for server_info in json_response:
                message_to_send += f'**{server_info['name']}**:\n\tStatus: {discordInlineCode(server_info['state'])}\n\tDomain: {discordInlineCode(server_info['domain'])}\n\n'

            await message.channel.send(message_to_send)
        elif subcommand == 'stopped':
            message_to_send = ', '.join([server_info['name'] for server_info in json_response if server_info['state'] == 'stopped'])

            if message_to_send:
                await message.channel.send(message_to_send)
            else:
                await message.channel.send('All servers are running.')
        elif subcommand == 'running':
            message_to_send = ', '.join([server_info['name'] for server_info in json_response if server_info['state'] == 'running'])

            if message_to_send:
                await message.channel.send(message_to_send)
            else:
                await message.channel.send('There are no servers running.')
        elif subcommand == 'available':
            message_to_send = ', '.join([server_info['name'] for server_info in json_response])

            await message.channel.send(message_to_send)
        else:
            await message.channel.send('Usage: ' + discordInlineCode(command_reference['list']['help']['usage']))
    else:
        await message.channel.send('Usage: ' + discordInlineCode(command_reference['list']['help']['usage']))

async def handleStart(message, message_tokens):
    if len(message_tokens) == 2:
        server = message_tokens[1]

        url = f'http://{server_domain}:8000/start/' + server
        json_response = json.loads(requests.post(url).text)

        if json_response[0] == 'Server started':
            await message.channel.send(f'**{server}** started!\nConnect at: `{server.lower()}.avyx.home`')
        elif json_response[0] == 'Server startup failed':
            await message.channel.send(f'**{server}** failed to start.')
        elif json_response[0] == 'Server already started':
            await message.channel.send('Server already started.')
        else:
            print(json_response)
            await message.channel.send('Something went horribly wrong. Contact an admin.')

    else:
        await message.channel.send('Usage: ' + discordInlineCode(command_reference['start']['help']['usage']))

# TODO: currently this will send "stop ENTER" to the tmux session, but if the server is not ready this may not work as intended
# need to check if server is ready
async def handleStop(message, message_tokens):
    if len(message_tokens) == 2:
        server = message_tokens[1]

        url = f'http://{server_domain}:8000/stop/' + server
        json_response = json.loads(requests.post(url).text)

        if json_response[0] == 'Server stopped':
            await message.channel.send(f'**{server}** stopped.')
        elif json_response[0] == 'Server stop failed':
            await message.channel.send(f'**{server}** failed to stop.')
        elif json_response[0] == 'Server already stopped':
            await message.channel.send('Server already stopped.')
        elif json_response[0] == 'Server does not exist':
            await message.channel.send('Server doesn\'t exist.')
        else:
            print(json_response)
            await message.channel.send('Something went horribly wrong. Contact an admin.')

    else:
        await message.channel.send('Usage: ' + discordInlineCode(command_reference['stop']['help']['usage']))

command_reference = {
    'help': {
        'handler': handleHelp,
        'is_privileged': False,
        'help': {
            'blurb': 'Lists available commands, how to use them, and what they do.',
            'usage': '/help [command]',
            'detailed': """
                        Argument syntax explanation:
                        \\- `[]` means the argument is optional
                        \\- `<>` means the argument is necessary
                        \\- `|`means or but not both and not neither (xor)
                        \\- `...` means unspecified number of arguments
                        """
        }
    },
    'activate': {
        'handler': handleActivate,
        'is_privileged': False,
        'help': {
            'blurb': 'Activate newton, the machine that will be running the Minecraft servers.',
            'usage': '/activate',
            'detailed': ''
        }
    },
    'register': {
        'handler': handleRegister,
        'is_privileged': True,
        'help': {
            'blurb': 'This is an admin command, it makes it easy for me to register servers with the bot.',
            'usage': '/register <server name> [server names...]',
            'detailed': ''
        }
    },
    'ping': {
        'handler': handlePing,
        'is_privileged': False,
        'help': {
            'blurb': 'Checks if either newton or the API are running.',
            'usage': '/ping [machine | api]',
            'detailed': """
                        Subcommands:
                        \\- `machine`: Check if newton itself is on.
                        \\- `api`: Check if the api is running.
                        Defaults to `machine` if no command is specified.
                        """
        }
    },
    'list': {
        'handler': handleList,
        'is_privileged': False,
        'help': {
            'blurb': 'Lists running and available servers along with their domains.',
            'usage': '/list <status | stopped | running | available>',
            'detailed': """
                        Subcommands:
                        \\- `status`: List all servers along with their state and domain.
                        \\- `stopped`: List servers that are stopped.
                        \\- `running`: List servers that are currently running.
                        \\- `available`: List servers that are available.
                        """
        }
    },
    'start': {
        'handler': handleStart,
        'is_privileged': False,
        'help': {
            'blurb': 'Starts the specified Minecraft server.',
            'usage': '/start <server name>',
            'detailed': 'Is case sensitive, so if you want RLCraft `/start rlcraft` will not work.'
        }
    },
    'stop': {
        'handler': handleStop,
        'is_privileged': False,
        'help': {
            'blurb': 'Stops the specified Minecraft server.',
            'usage': '/stop <server name>',
            'detailed': 'Is case sensitive, so if you want to stop Cobbleverse `/stop cobbleverse` will not work.'
        }
    },
    'lock': {
        'handler': handleLock,
        'is_privileged': True,
        'help': {
            'blurb': 'Prevents any commands from being carried out until lock is released.',
            'usage': '/lock',
            'detailed': 'Privileged command.'
        }
    },
    'release': {
        'handler': handleRelease,
        'is_privileged': True,
        'help': {
            'blurb': 'Releases lock.',
            'usage': '/release',
            'detailed': 'Privileged command.'
        }
    }
}

client = MyClient()
client.run(token)

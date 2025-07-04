admins = ['avvyxx']
registered_servers = set()

import discord, textwrap, subprocess, sys

def getUsername(UserorMember):
    return str(UserorMember).split('#')[0]

def discordInlineCode(s):
    return f'`{s}`'

class MyClient(discord.Client):
    async def on_read(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        if message.author != self.user:
            # check if message is command
            if message.content:
                if (message.content[0] == '/'):
                    message_tokens = message.content[1:].split()

                    try:
                        await handleCommand(message, message_tokens)
                    except Exception as e:
                        # TODO: Ping me, or everyone in admins list
                        await message.channel.send(f'There seems to have been an error: `{type(e).__name__}: {str(e)}`')
                        await message.channel.send('idk how to make it ping me yet so someone else do it')
            else:
                await message.channel.send(f'Somehow {getUsername(message.author)} managed to send an empty message.')

async def handleCommand(message, message_tokens):
    if not message_tokens:
        return

    command = message_tokens[0]

    if command in command_reference:
        await command_reference[command]['handler'](message, message_tokens)

    else:
        await message.channel.send('Unkown command: ' + command)

# list all for /help
# list specified for /help <command>
async def handleHelp(message, message_tokens):
    if len(message_tokens) == 1:
        message_to_send = 'Available commands:\n'

        for command in command_reference:
            message_to_send += f'\- {discordInlineCode(command)}: {command_reference[command]['help']['blurb']}\n'

        message_to_send += 'Try: `/help list`'

        await message.channel.send(message_to_send)
    elif len(message_tokens) == 2:
        help_command = message_tokens[1]

        if help_command in command_reference:
            help_reference = command_reference[help_command]['help']

            message_to_send = help_reference['blurb'].strip() + '\n'

            if help_reference['detailed']:
                message_to_send += '\n' + textwrap.dedent(help_reference['detailed']).strip() + '\n\n'
            else:
                message_to_send += '\n'

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
    await message.channel.send('activating machine')

# check if newton is responding
# should wait a certain amount of time before deciding newton is not responding
async def handlePing(message, message_tokens):
    await message.channel.send('pinging newton')

# list with an extra set of commands
# list running
# list available
# list: usage <running | available>
async def handleList(message, message_tokens):
    if len(message_tokens) == 2:
        subcommand = message_tokens[1]

        if subcommand == 'all':
            await message.channel.send('Listing all servers')
        elif subcommand == 'stopped':
            await message.channel.send('Listing all stopped servers')
        elif subcommand == 'running':
            for server in registered_servers:
                # check if server is running
                pass

            await message.channel.send('listing running servers')
        elif subcommand == 'available':
            await message.channel.send('Available servers: ' + ', '.join(registered_servers))
        else:
            await message.channel.send('Usage: ' + command_reference['list']['help']['usage'])
    else:
        await message.channel.send('Usage: ' + command_reference['list']['help']['usage'])

command_reference = {
    'help': {
        'handler': handleHelp,
        'help': {
            'blurb': 'Lists available commands, how to use them, and what they do.',
            'usage': '/help [command]',
            'detailed': """
                        Argument syntax explanation:
                        \- `[]` means the argument is optional
                        \- `<>` means the argument is necessary
                        \- `|`means or but not both and not neither (xor)
                        \- `...` means unspecified number of arguments
                        """
        }
    },
    'activate': {
        'handler': handleActivate,
        'help': {
            'blurb': 'Activate newton, the machine that will be running the Minecraft servers.',
            'usage': '/activate',
            'detailed': ''
        }
    },
    'register': {
        'handler': handleRegister,
        'help': {
            'blurb': 'This is an admin command, it makes it easy for me to register servers with the bot.',
            'usage': '/register <server name> [server names...]',
            'detailed': ''
        }
    },
    'ping': {
        'handler': handlePing,
        'help': {
            'blurb': 'This is a temporary command that you can use to know if newton is on or not.',
            'usage': '/ping [amount of time to wait in seconds]',
            'detailed': 'TODO: `/activate` should message the server when newton wakes up.'
        }
    },
    'list': {
        'handler': handleList,
        'help': {
            'blurb': 'Lists running and available servers along with their domains.',
            'usage': '/list <running | available>',
            'detailed': """
                        Subcommands:
                        \- `all`: List all servers along with their state.
                        \- `stopped`: List servers that are stopped.
                        \- `running`: List servers that are currently running.
                        \- `available`: List servers that are available.
                        """
        }
    }
}

client = MyClient()
client.run(token)

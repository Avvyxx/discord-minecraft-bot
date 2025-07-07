import subprocess, json, requests

def getUsername(UserorMember):
    return str(UserorMember).split('#')[0]

def discordInlineCode(s):
    return f'`{s}`'

def ping_machine(domain):
    result = subprocess.run('ping -c 1 ' + domain, shell=True, executable='/bin/bash')

    return result.returncode == 0

def ping_api(domain):
    url = f'http://{domain}:8000/ping'
    json_response = json.loads(requests.get(url).text)

    return json_response[0] == 'pong'

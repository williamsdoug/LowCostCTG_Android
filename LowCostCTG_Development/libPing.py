# from: https://stackoverflow.com/questions/2953462/pinging-servers-in-python

from platform   import system as system_name  # Returns the system/OS name
from subprocess import call   as system_call  # Execute a shell command

def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    print system_name().lower()

    # Ping command count option as function of OS
    param = '-n' if system_name().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    # Pinging
    return system_call(command) == 0

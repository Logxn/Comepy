import os
import sys
import keyring
from getpass import getpass
from colorama import *
from comdirect import Comdirect

NAMESPACE = 'comdirect-manager-dev'

INFO = Fore.CYAN
HIGHLIGHT = Fore.MAGENTA
SUCCESS = Fore.GREEN
WARN = Fore.YELLOW
ERR = Fore.RED
RESET = Fore.RESET


def __cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def __keyring_available() -> bool:
    return keyring.get_credential(NAMESPACE, 'Zugangsnummer') is not None


def __ask_for_agreement() -> bool:
    valid_inputs = ['y', 'N']
    user_input = None

    while user_input not in valid_inputs:
        __cls()
        print(f'{HIGHLIGHT}-- Configuration --')
        print(f'[\N{gear}] {INFO}We didn\'t detect any user-data stored on this machine.')
        print(f'[\N{gear}] {INFO}To continue, you will need to enter a set of user informations.')
        print(f'[\N{gear}] {INFO}Your data will be stored in your {HIGHLIGHT}system default{INFO} keychain!')
        user_input = input(f'[\N{question mark}] {INFO}Do you want to continue? [y/N]:{RESET} ')

    return user_input == 'y'


def __ask_for_access_number() -> str:
    access_number = ''
    while len(access_number) != 8:
        access_number = input(f'[\N{key}] {INFO}Please provide the 8-digit {HIGHLIGHT}access number:{RESET} ')

    return access_number


def __ask_for_personal_pin() -> str:
    personal_pin = ''
    while len(personal_pin) != 6:
        print(f'[\N{key}] {INFO}Please provide the 6-digit {HIGHLIGHT}personal pin {INFO}(Input hidden):{RESET} ', end='')
        personal_pin = getpass('')

    return personal_pin


def __ask_for_client_id() -> str:
    client_id = None
    while not client_id:
        client_id = input(f'[\N{key}] {INFO}Please provide the API {HIGHLIGHT}client-id:{RESET} ')

    return client_id


def __ask_for_client_secret() -> str:
    client_secret = None
    while not client_secret:
        client_secret = input(f'[\N{key}] {INFO}Please provide the API {HIGHLIGHT}client-secret:{RESET} ')

    return client_secret


def __setup_keyring() -> bool:
    agreed = __ask_for_agreement()

    if not agreed:
        print(f'[\N{cross mark}] {ERR}User aborted setup. Goodbye.')
        sys.exit(0)

    access_number = __ask_for_access_number()
    personal_pin = __ask_for_personal_pin()
    client_id = __ask_for_client_id()
    client_secret = __ask_for_client_secret()

    keyring.set_password(NAMESPACE, 'Zugangsnummer', access_number)
    keyring.set_password(NAMESPACE, access_number, personal_pin)
    keyring.set_password(NAMESPACE, 'ClientId', client_id)
    keyring.set_password(NAMESPACE, 'ClientSecret', client_secret)

    __cls()

    print(f'[\N{check mark}] {SUCCESS}Setup complete.')

    return True


def main():
    # Color logging
    init(autoreset=True)

    print(f'{HIGHLIGHT}< Comdirect API Test >')
    configuration_available = __keyring_available()

    if not configuration_available:
        __setup_keyring()
    else:
        print(f'[\N{sparkles}] {SUCCESS}Welcome back!')

    com = Comdirect()
    


if __name__ == '__main__':
    main()

import uuid
import keyring
import sys
import json
import time
from requestclient import RequestClient
from apscheduler.schedulers.background import BlockingScheduler
from colorama import *

NAMESPACE = 'comdirect-manager'

INFO = Fore.CYAN
HIGHLIGHT = Fore.MAGENTA
SUCCESS = Fore.GREEN
WARN = Fore.YELLOW
ERR = Fore.RED
RESET = Fore.RESET


class Comdirect:
    def __init__(self):
        self.__access_token = keyring.get_password(NAMESPACE, 'Zugangsnummer')
        self.__personal_pin = keyring.get_credential(NAMESPACE, self.__access_token).password
        self.__client_id = keyring.get_password(NAMESPACE, 'ClientId')
        self.__client_secret = keyring.get_password(NAMESPACE, 'ClientSecret')

        self.__COM_BASEURL = 'https://api.comdirect.de'
        self.__OAUTH_ENDPOINT = self.__COM_BASEURL + '/oauth'
        self.__TOKEN_ENDPOINT = self.__OAUTH_ENDPOINT + '/token'
        self.__SESSIONS_STATUS_ENDPONT = self.__COM_BASEURL + f'/api/session/clients/{self.__client_id}/v1/sessions'
        self.__SESSION_VALIDATE_ENDPOINT = self.__COM_BASEURL
        self.__ACTIVATE_TAN_ENDPOINT = self.__COM_BASEURL

        self.__request_client = RequestClient()
        self.__endpoint_access_token = None
        self.__endpoint_refresh_token = None
        self.__get_token()

        self.kunden_nummer = None
        self.session_id = None

    def __get_token(self):
        data = {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'password',
            'username': self.__access_token,
            'password': self.__personal_pin
        }

        response = self.__request_client.post_urlencoded(self.__TOKEN_ENDPOINT, data)

        if response.status_code != 200:
            print(f'{ERR}Failed to receive access_token! Wrong API Data?')
            sys.exit(1)

        content_decoded = response.content.decode('utf-8').replace("'", '"')
        content = json.loads(content_decoded)

        self.kunden_nummer = content['kdnr']

        access_token = content['access_token']
        self.__endpoint_access_token = access_token
        self.__request_client.update_headers(access_token)

        self.__get_sessions()

    def __get_sessions(self):
        request_info = {
            'clientRequestId': {
                'sessionId': f'{uuid.uuid4()}',
                'requestId': f'{round(time.time() * 1000)}'
            }
        }

        response = self.__request_client.get(self.__SESSIONS_STATUS_ENDPONT, auth=True, request_info=request_info)

        if response.status_code == 404:
            print(f'[\N{cross mark}] {ERR}Failed to receive session status! Authorization failed!')
            sys.exit(1)
        elif response.status_code != 200:
            print(f'[\N{cross mark}] {ERR}Failed to receive session status! ({response.status_code}) Unknown Error')
            print(response.content)
            sys.exit(1)

        content_decoded = response.content.decode('utf-8').replace("'", '"')
        content = json.loads(content_decoded)

        self.session_id = content[0]['identifier']

        # Updating the endpoint here, since this is the first time our session_id is known.
        self.__SESSION_VALIDATE_ENDPOINT += f"/api/session/clients/{self.__client_id}/v1/sessions/{self.session_id}/validate"
        self.__ACTIVATE_TAN_ENDPOINT += f'/api/session/clients/{self.__client_id}/v1/sessions/{self.session_id}'

        self.__validate_session()

    def __validate_session(self):
        request_info = {
            'clientRequestId': {
                'sessionId': self.session_id,
                'requestId': str(round(time.time() * 1000))
            }
        }

        json_data = {
            'identifier': self.session_id,
            'sessionTanActive': True,
            'activated2FA': True
        }

        response = self.__request_client.post_json(self.__SESSION_VALIDATE_ENDPOINT, json_data, auth=True, request_info=request_info)

        if response.status_code != 201:
            print(f'[\N{cross mark}] {ERR}Failed to validate session! ({response.status_code})')
            # print(f'[\N{cross mark}] {ERR}{response.content}')
            sys.exit(1)

        once_auth_info = json.loads(response.headers['x-once-authentication-info'])

        input(f'[\N{key}] {INFO}Please confirm your login over the {HIGHLIGHT}photoTAN App {INFO}on your Phone! (Press enter when ready){RESET}')
        time.sleep(5)

        self.__activate_tan(once_auth_info['id'])

    def __activate_tan(self, challenge_id):
        request_info = {
            'clientRequestId': {
                'sessionId': self.session_id,
                'requestId': str(round(time.time() * 1000))
            }
        }

        request_body = {
            'identifier': self.session_id,
            'sessionTanActive': True,
            'actiated2FA': True
        }

        response = self.__request_client.patch(self.__ACTIVATE_TAN_ENDPOINT, json_data=request_body, request_info=request_info, tan_id=challenge_id, tan='123456')

        if response.status_code != 200:
            print(f'[\N{cross mark}] {ERR}Failed to validate TAN! ({response.status_code})')
            # print(f'{ERR}{response.content}')
            sys.exit(1)

        print(f'[\N{key}] {SUCCESS}TAN validated!')

        self.__update_token()

    def __update_token(self):
        form_data = {
            'client_id': {self.__client_id},
            'client_secret': {self.__client_secret},
            'grant_type': 'cd_secondary',
            'token': {self.__endpoint_access_token}
        }

        response = self.__request_client.post_urlencoded(self.__TOKEN_ENDPOINT, form_data)

        if response.status_code != 200:
            print(f'[\N{cross mark}] {ERR}Failed to receive secondary access token! ({response.status_code})')
            # print(f'[\N{cross mark}] {ERR}{response.content}')
            sys.exit()

        content_decoded = response.content.decode('utf-8').replace("'", '"')
        content = json.loads(content_decoded)

        access_token = content['access_token']
        self.__endpoint_access_token = access_token
        self.__request_client.update_headers(access_token)

        refresh_token = content['refresh_token']
        self.__endpoint_refresh_token = refresh_token

        expires_in = content['expires_in']

        print(f'[\N{key}] {SUCCESS}Logged in with customer number <{self.kunden_nummer}>! {HIGHLIGHT} => {access_token} \N{sparkles}')

        # Start the timer to refresh the token
        # Token is valid for 9,98 Minutes
        # We will still update the token a little bit earlier
        scheduler = BlockingScheduler()
        scheduler.add_job(self.__refresh_token, 'interval', seconds=(expires_in - 10))
        scheduler.start()

    def __refresh_token(self):
        form_data = {
            'client_id': self.__client_id,
            'client_secret': self.__client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': self.__endpoint_refresh_token
        }

        response = self.__request_client.post_urlencoded(self.__TOKEN_ENDPOINT, form_data)

        if response.status_code != 200:
            print(f'[\N{cross mark}] {ERR}Failed to refresh access_token! ({response.status_code})')
            # print(f'[\N{cross mark}] {ERR}{response.content}')
            sys.exit()

        content_decoded = response.content.decode('utf-8').replace("'", '"')
        content = json.loads(content_decoded)

        access_token = content['access_token']
        self.__endpoint_access_token = access_token
        self.__request_client.update_headers(access_token)

        refresh_token = content['refresh_token']
        self.__endpoint_refresh_token = refresh_token

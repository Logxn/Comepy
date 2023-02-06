import requests as r
import time


class RequestClient:
    def __init__(self):
        self.default_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        self.auth_headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

    def __get_timestamp(self) -> int:
        return round(time.time() * 1000)

    def update_headers(self, access_token):
        self.auth_headers['Authorization'] = f'Bearer {access_token}'

    def post_urlencoded(self, url, data, auth=False, request_info=None):
        response = None
        sending_headers = self.auth_headers

        if auth:
            if request_info:
                sending_headers['x-http-request-info'] = str(request_info)
            response = r.post(url, data=data, headers=self.auth_headers)
        else:
            response = r.post(url, data=data, headers=self.default_headers)

        return response

    def post_json(self, url, data, auth=False, request_info=None, extra_header=None):
        response = None
        sending_headers = self.auth_headers

        if extra_header:
            key = list(extra_header)[0]
            sending_headers[key] = str(extra_header[key])

        if auth:
            if request_info:
                sending_headers['x-http-request-info'] = str(request_info)
            response = r.post(url, json=data, headers=self.auth_headers)
        else:
            response = r.post(url, json=data, headers=self.default_headers)

        return response

    def get(self, url, auth=False, request_info=None):
        response = None
        sending_headers = self.auth_headers
        sending_headers['Content-Type'] = 'application/json'

        if auth:
            if request_info:
                sending_headers['x-http-request-info'] = str(request_info)
            response = r.get(url, headers=sending_headers)
        else:
            response = r.get(url, headers=self.default_headers)

        return response

    def patch(self, url, json_data, request_info=None, tan_id=None, tan=None):
        response = None
        sending_headers = self.auth_headers

        if request_info:
            sending_headers['x-http-request-info'] = str(request_info)

        if id and tan:
            sending_headers['x-once-authentication-info'] = f'{{"id":"{tan_id}"}}'
            sending_headers['x-once-authentication'] = '123456'

        response = r.patch(url, json=json_data, headers=sending_headers)

        return response

    def delete(self, url):
        sending_headers = self.default_headers
        sending_headers['Authorization'] = self.auth_headers['Authorization']

        response = r.delete(url, headers=sending_headers)

        return response

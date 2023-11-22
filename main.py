import requests
import time
import json

MAILTM_HEADERS = {   
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpYXQiOjE3MDA2NDIzNDcsInJvbGVzIjpbIlJPTEVfVVNFUiJdLCJhZGRyZXNzIjoicmVuem8xMjM0NUBobGRyaXZlLmNvbSIsImlkIjoiNjU1ZGJkZjJhZjVmZTg1MDViMGIzNjAyIiwibWVyY3VyZSI6eyJzdWJzY3JpYmUiOlsiL2FjY291bnRzLzY1NWRiZGYyYWY1ZmU4NTA1YjBiMzYwMiJdfX0.3fzyAySJ2W5EsNEWRL4dS37AkDx3ALQDO6ianJJMkm15wb5e1KA98Jka59PhqY5VDYWcG1HqwiMPYbRT7H6UJg"
}

class MailTmError(Exception):
    pass

def _make_mailtm_request(request_fn, timeout = 600):
    tstart = time.monotonic()
    error = None
    status_code = None
    while time.monotonic() - tstart < timeout:
        try:
            r = request_fn()
            status_code = r.status_code
            if status_code == 200 or status_code == 201:
                return r.json()
            if status_code != 429:
                break
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            error = e
        time.sleep(1.0)
    
    if error is not None:
        raise MailTmError(e) from e
    if status_code is not None:
        raise MailTmError(f"Status code: {status_code}")
    if time.monotonic() - tstart >= timeout:
        raise MailTmError("timeout")
    raise MailTmError("unknown error")

def get_mailtm_domains():
    def _domain_req():
        return requests.get("https://api.mail.tm/domains", headers = MAILTM_HEADERS)
    
    r = _make_mailtm_request(_domain_req)

    return [ x['domain'] for x in r ]

def create_mailtm_account(address, password):
    account = json.dumps({"address": address, "password": password})   
    def _acc_req():
        return requests.post("https://api.mail.tm/accounts", data=account, headers=MAILTM_HEADERS)

    r = _make_mailtm_request(_acc_req)
    assert len(r['id']) > 0

def get_mailtm_messages(page = 1):
    def _domain_req():
        return requests.get(f'https://api.mail.tm/messages?pages={page}', headers = MAILTM_HEADERS)
    r = _make_mailtm_request(_domain_req)
    return r

def parse_to(to):
    return to["address"]   

def parse_headers(message):
    return json.dumps({"id": message["id"], "createdAt": message["createdAt"], "subject": message["subject"], "from": message["from"]["address"], "to": list(map(parse_to, message["to"])) })    

stored_email_id = []

def parse_ids(message):
    return message["id"]   

def filter_messages(message):
    if message["id"] in stored_email_id:
        return False
    else:
        return True;

def parse_messages(message):
    return json.dumps({ "from": message["from"]["address"] , "subject": message["subject"], "intro": message["intro"],})    

while(True): 
    filtered = list(filter(filter_messages, list(get_mailtm_messages())))
    mapped = list(map(parse_messages, list(filtered)))
    print(mapped)
    stored_email_id = set(list([*map(parse_ids, get_mailtm_messages()), *stored_email_id]))
    time.sleep(5) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  EspoCRM util functions.

from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateutil.parser
import email.utils
import json
import requests
import os
import sys
from typing import Any, List, Dict

BASE_URL = os.environ["ESPOCRM_BASE_URL"]
API_KEY = os.environ["ESPOCRM_API_KEY"]

REMINDER_FROM_EMAIL = os.environ["ESPOCRM_REMINDER_FROM"]
REMINDER_TO_EMAIL = os.environ["ESPOCRM_REMINDER_TO"]

NUM_DAYS = 10

@dataclass
class PersonInfo:
    idStr: str
    contactType: str
    name: str
    email: str
    lastModified: str

    @property
    def url(self) -> str:
        return BASE_URL + f"/#{self.contactType}/view/{self.idStr}"

    def to_line(self) -> str:

        return f"- {self.name} <{self.email}>: last interaction {self.lastModified} - {self.url}"

    def last_activity_within(self) -> bool:
        endpoint = f"/api/v1/Activities/{self.contactType}/{self.idStr}/history"

        r = requests.get(BASE_URL + endpoint,
            headers={'X-Api-Key': API_KEY},
            params={
                'maxSize': '2',
                'orderBy': 'dateStart',
                'order': 'desc',
            },
        )

        resp = json.loads(r.text)
        assert isinstance(resp, dict)
        lst = resp['list']
        assert isinstance(lst, list)

        if len(lst) < 1:
            return False

        last_activity = dateutil.parser.isoparse(lst[0]['dateStart'])

        ret = last_activity >= (datetime.today() - relativedelta(days=NUM_DAYS))
        if ret:
            print(f"{self.url} has recent activity; lastModified = {self.lastModified}")
        return ret

def get_old_leads() -> List[PersonInfo]:
    endpoint = "/api/v1/Lead"

    r = requests.get(BASE_URL + endpoint,
        headers={'X-Api-Key': API_KEY},
        params={
            'select': 'name,emailAddress,modifiedAt',
            'orderBy': 'modifiedAt',
            'order': 'asc',
            'where[0][type]': 'olderThanXDays',
            'where[0][attribute]': 'modifiedAt',
            'where[0][value]': str(NUM_DAYS),
            'where[1][type]': 'notIn',
            'where[1][attribute]': 'status',
            'where[1][value][]': 'Converted',
            'where[1][value][]': 'Dead',
        },
    )
    if r.status_code != 200:
        print(repr(r), file=sys.stderr)
        raise ValueError("An error occurred")

    def conv(x: Dict[str, Any]) -> PersonInfo:
        return PersonInfo(
            idStr = str(x['id']),
            contactType = "Lead",
            name = str(x['name']),
            email = str(x['emailAddress']),
            lastModified = str(x['modifiedAt']),
        )

    resp = json.loads(r.text)
    assert isinstance(resp, dict)
    lst = resp['list']
    assert isinstance(lst, list)

    return list(map(conv, lst))

def get_old_contacts() -> List[PersonInfo]:
    endpoint = "/api/v1/Contact"

    r = requests.get(BASE_URL + endpoint,
        headers={'X-Api-Key': API_KEY},
        params={
            'select': 'name,emailAddress,modifiedAt',
            'orderBy': 'modifiedAt',
            'order': 'asc',
            'where[0][type]': 'olderThanXDays',
            'where[0][attribute]': 'modifiedAt',
            'where[0][value]': str(NUM_DAYS),
        },
    )
    if r.status_code != 200:
        print(repr(r), file=sys.stderr)
        raise ValueError("An error occurred")

    def conv(x: Dict[str, Any]) -> PersonInfo:
        return PersonInfo(
            idStr = str(x['id']),
            contactType = "Contact",
            name = str(x['name']),
            email = str(x['emailAddress']),
            lastModified = str(x['modifiedAt']),
        )

    resp = json.loads(r.text)
    assert isinstance(resp, dict)
    lst = resp['list']
    assert isinstance(lst, list)

    return list(map(conv, lst))

def build_body(lst: List[PersonInfo]) -> str:
    resp = "Dear team,\n\n"
    resp += f"The following CRM entries have not seen interaction for more than {NUM_DAYS} days:\n\n"

    for p in lst:
        resp += p.to_line() + "\n"

    resp += "\n"
    resp += "Cheers,\n"
    resp += "Your friendly CRM"
    return resp

def send_email(subject: str, body: str) -> None:
    endpoint = "/api/v1/Email"

    r = requests.post(BASE_URL + endpoint,
        headers={'X-Api-Key': API_KEY},
        json={
            "status": "Sending",
            "isRead": True,
            "isImportant": False,
            "inTrash": False,
            "folderId": False,
            "isUsers": False,
            "isHtml": False,
            "isSystem": False,
            "isJustSent": False,
            "to": REMINDER_TO_EMAIL,
            "subject": subject,
            "name": subject,
            "body": body,
            "bodyPlain": body,
            "from": REMINDER_FROM_EMAIL,
            "cc":"","bcc":"",
            "parentType": None,
            "parentName": None,
            "parentId": None,
            "selectTemplateName": None,
            "selectTemplateId": None,
            "attachmentsIds": [],
        },
    )
    print(f"send_email DEBUG: {r}")

@dataclass
class IngestedEmail:
    # ISO 8601
    date_sent: str

    fromStr: str

    # Semi-colon separated
    to: str
    cc: str
    subject: str

    body: str

    @staticmethod
    def from_str(instr: str) -> "IngestedEmail":
        return IngestedEmail.from_json(json.loads(instr))

    @staticmethod
    def from_json(json: Dict[str, str]) -> "IngestedEmail":
        # Example
        # {"dateRaw":"2021-05-05T05:05:05.000Z","fromRaw":"Name <name@example.com>","toRaw":"Foo Foo <foo@example.com>, Bar Bar <bar@example.com>","ccRaw":"Aa Aa <a@example.com>, Bb Bb <b@example.com>","subjectRaw":"Subject","bodyRaw":"Body Body"}

        fromStr = email.utils.parseaddr(str(json["fromRaw"]))[1]
        toList = list(map(lambda x: x[1], email.utils.getaddresses([str(json["toRaw"])])))
        to = ";".join(toList)
        ccList = list(map(lambda x: x[1], email.utils.getaddresses([str(json["ccRaw"])])))
        cc = ";".join(ccList)

        return IngestedEmail(
            date_sent=dateutil.parser.isoparse(json["dateRaw"]).strftime("%Y-%m-%d %H:%M:%S"),
            fromStr=fromStr,
            to=to,
            cc=cc,
            subject=str(json["subjectRaw"]),
            body=str(json["bodyRaw"]),
        )

EXAMPLE_INGESTED_EMAIL = IngestedEmail(
    date_sent="2022-06-11 15:12:12",
    fromStr="foobar@example.com",
    to="dest@example.com",
    cc="a@example.com;b@example.com",
    subject="My Subject",
    body="My Body",
)

def register_email(eml: IngestedEmail) -> None:
    endpoint = "/api/v1/Email"

    r = requests.post(BASE_URL + endpoint,
        headers={'X-Api-Key': API_KEY},
        json={
            "status": "Archived",
            "isRead": True,
            "isImportant": False,
            "inTrash": False,
            "folderId": False,
            "isUsers": False,
            "isHtml": False,
            "isSystem": False,
            "isJustSent": False,
            "dateSent": eml.date_sent,
            "to": eml.to,
            "subject": eml.subject,
            "name": eml.subject,
            "body": eml.body,
            "bodyPlain": eml.body,
            "from": eml.fromStr,
            "cc": eml.cc,
            "bcc": "",
            "parentType": None,
            "parentName": None,
            "parentId": None,
            "selectTemplateName": None,
            "selectTemplateId": None,
            "attachmentsIds": [],
        },
    )
    print(f"send_email DEBUG: {r}")

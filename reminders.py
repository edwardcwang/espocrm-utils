#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  reminders.py
#  Send some reminders for old contacts/leads.
#
#  Requires an API key including Activities, Contacts, Leads, Emails,
#  Calls, Meetings, Documents.

from espocrm_utils import *
from typing import *

SEND_EMAIL = int(os.environ.get("ESPOCRM_SEND_EMAIL", "1")) > 0

def main(args: List[str]) -> int:

    leads = get_old_leads()
    contacts = get_old_contacts()

    ppl = leads + contacts

    ppl = list(filter(lambda x: not x.last_activity_within(), ppl))

    if len(ppl) < 1:
        print("Nothing needs to be poked")
        return 0

    subject = "Reminder - CRM"
    body = build_body(ppl)

    print("=== E-mail body ===")
    print(body)

    if SEND_EMAIL:
        send_email(subject=subject, body=body)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))

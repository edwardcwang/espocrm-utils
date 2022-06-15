EspoCRM Utilities
=================

This repo contains two utilities for EspoCRM - 1) an automatic reminder e-mail sender for inactive contacts and leads; 2) an ingestion endpoint for pushing e-mail metadata into EspoCRM.

Tested with EspoCRM 7.1.7.

To run, build it with `docker build -t espocrm_utils .`

Then run it as below (examples):

```shell
# For reminders
docker run --name espocrm_utils-instance \
  -e ESPOCRM_BASE_URL=http://192.168.0.1 -e ESPOCRM_API_KEY=abcdef -e ESPOCRM_REMINDER_FROM=crm@example.com -e ESPOCRM_REMINDER_TO=team@example.com \
  -d -it espocrm_utils

# For e-mail ingestion
docker run --name espocrm_utils-instance \
  -e ESPOCRM_BASE_URL=http://192.168.0.1 -e ESPOCRM_API_KEY=abcdef -e ESPOCRM_REMINDER_FROM=crm@example.com -e ESPOCRM_REMINDER_TO=team@example.com \
  -d -it espocrm_utils /opt/ingest_email.py 8080
```

Requires the following environment variables:

* `ESPOCRM_BASE_URL` - base URL to the EspoCRM instance. Used for connecting to the API.
* `ESPOCRM_DISP_URL` - (optional) base URL to use for generating links
* `ESPOCRM_API_KEY` - the [EspoCRM API key](https://docs.espocrm.com/development/api/#authentication-by-api-key).
* `REMINDER_FROM_EMAIL` - from e-mail address to use for the reminder e-mail. Should be the sender e-mail address configured for the system in EspoCRM.
* `REMINDER_TO_EMAIL` - where to send the reminder e-mail.
* `ESPOCRM_SEND_EMAIL` - (optional, for debugging) set to 0 to disable actually sending e-mail
* `ESPOCRM_REGISTER_EMAIL` - (optional, for debugging) set to 0 to disable actually registering incoming e-mails with EspoCRM

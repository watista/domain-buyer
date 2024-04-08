#!/usr/bin/python3

#   This file is owned by Paas IT
#   Author: Wouter Paas <wouter@paasit.net>
#   Date 08-12-2022

from dotenv import load_dotenv
import time
import json
import argparse
import logging
import os
import requests
import whois
import tldextract
from telegram import Bot


def setLogging(consoleLogging=False):

    # Set logging format and config
    logging.root.handlers = []
    if os.getenv("LOG_TYPE") == "DEBUG":
        fmt = "%(levelname)s:%(name)s:%(asctime)s - %(message)s - {%(pathname)s:%(lineno)d}"
    else:
        fmt = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
    logging.basicConfig(filename="main.log", level=logging.os.getenv("LOG_TYPE"), format=fmt, datefmt='%d-%m-%Y %H:%M:%S')

    # Set console logging
    if consoleLogging:
        console = logging.StreamHandler()
        console.setLevel(logging.os.getenv("LOG_TYPE"))
        console.setFormatter(logging.Formatter(fmt))
        logging.getLogger("").addHandler(console)


def sendMessage(dtype, msg, telegram=True):

    if telegram:
        try:
            Bot(os.getenv('BOT_TOKEN')).send_message(chat_id="414578726", text=msg, parse_mode="Markdown", disable_web_page_preview=True, disable_notification=False, timeout=5)
        except Exception as e:
            logging.error(f"Error while sending Telegram message: {e}")

    # Prettify
    msg = msg.encode('ascii', 'ignore').decode('ascii')
    msg = msg.replace("\n", " - ")
    msg = msg.replace("*", "")
    msg = msg.replace("`", "")
    msg = msg.replace("  ", " ")
    msg = msg.strip()

    # Log according to type
    if dtype == "error":
        logging.error(msg)
    elif dtype == "warning":
        logging.warning(msg)
    elif dtype == "info":
        logging.info(msg)
    else:
        logging.debug(msg)


def tokenCheck():

    # Set tokens global
    global token_timestamp
    global token

    # Check if token is valid
    if not (token_timestamp + 3600) >= round(time.time()):

        # Get new token
        url = "https://api.openprovider.eu/v1beta/auth/login"
        payload = json.dumps({"username": os.getenv('USERNAME'),"password": os.getenv('PASSWORD')})

        try:
            # Make the request
            response = requests.request("POST", url, headers={'Content-Type': 'application/json'}, data=payload)
            if not response.ok:
                sendMessage("error", f"❌ *Error while fetching new Openprovider token* ❌\nError: *{response.status_code} {response.reason}*")
                return False

        except Exception as e:
            sendMessage("error", f"Error during get Openprovider token\nError: {' '.join(e.args)}")
            return False

        # Write token
        token = json.loads(response.text)['data']['token']
        token_timestamp = round(time.time())

    return True


if __name__ == '__main__':

    # Parse arguments and console logging if enabled
    parser = argparse.ArgumentParser(description='Openprovider Domain Buyer Script')
    parser.add_argument('--verbose', action='store_true', help='Enable console logging')
    parser.add_argument('-v', action='store_true', help='Enable console logging')
    args = parser.parse_args()
    console = args.v or args.verbose

    # Defaults
    load_dotenv()
    setLogging(console)
    token_timestamp = 0

    # Start
    while True:
        time.sleep(15)

        if not tokenCheck():
            continue

        for hostname in json.load(open('sites.json','r'))["sites"]:

            # Check Whois domain status, skip domain if active or uknown status
            w = whois.whois(hostname)
            if w['status'] == "in quarantine":
                sendMessage("info", f"WhoIs domain {hostname} is still in quarantine until {w['expiration_date']}", False)
            elif w['status'] == None:
                sendMessage("info", f"WhoIs domain {hostname} is free")
            elif w['status'] == "active":
                sendMessage("info", f"WhoIs domain {hostname} is already bought since {w['creation_date']}")
                continue
            else:
                sendMessage("warning", f"Unknown WhoIs domain status for {hostname}, status is: {w['status']}", False)
                continue


            # Check domain status at Openprovider
            domain = tldextract.extract(hostname)
            payload = json.dumps({"domains": [{"extension": domain.suffix, "name": domain.domain}]})
            try:
                # Make the request
                response = requests.request("POST", "https://api.openprovider.eu/v1beta/domains/check", headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, data=payload)
                if not response.text:
                    sendMessage("error", f"❌ *Error while status checking {hostname}* ❌\nError: *{response.status_code} {response.reason}*")
                    continue

                # Check json status codes, skip if active or unknown
                text = json.loads(response.text)
                if not text['code'] == 0:
                    sendMessage("warning", f"Unknown Openprovider error code for domain check {hostname}\nError code: {text['code']}\nDescription: {text['desc']}")
                    continue

                if text['data']['results'][0]['status'] == "active":
                    sendMessage("info", f"Domain {hostname} is still registered", False)
                    continue
                elif text['data']['results'][0]['status'] == "free":
                    sendMessage("info", f"Domain {hostname} is free, time to buy!")
                else:
                    sendMessage("warning", f"Unknown Openprovider domain check for {hostname}\nError code: {text['code']}\nDescription: {text['desc']}")
                    continue

            except Exception as e:
                sendMessage("error", f"Error during domain check {hostname}\nError: {e}")
                continue


            # Register domain at Openprovider
            payload = json.dumps({"domain": {"extension": domain.suffix, "name": domain.domain}, "admin_handle": "WP906887-NL", "owner_handle": "WP906887-NL", "tech_handle": "WP906887-NL", "billing_handle": "WP906887-NL", "reseller_handle": "WP906887-NL", "period": 1})
            try:
                # Make the request
                response = requests.request("POST", "https://api.openprovider.eu/v1beta/domains", headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, data=payload)
                if not response.text:
                    sendMessage("error", f"❌ *Error while ordering {hostname}* ❌\nError: *{response.status_code} {response.reason}*")
                    continue

                # Check json status codes
                text = json.loads(response.text)
                if text['code'] == 0:
                    sendMessage("info", f"✅ *Bought domain {hostname}* ✅")
                elif text['code'] == 311:
                    sendMessage("info", f"Domain {hostname} is still registered. Description: {text['desc']}", False)
                else:
                    sendMessage("warning", f"Unknown Openprovider error code for domain buy {hostname}\nError code: {text['code']}\nDescription: {text['desc']}")

            except Exception as e:
                sendMessage("error", f"Error during domain order {hostname}\nError: {e}")

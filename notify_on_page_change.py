"""
notify_on_page_change v1.0

Monitors web pages for changes that appear when the webpage is printed in a text-only
format.

Does not monitor visual changes that would occur otherwise. Does not currently allow
passing in login information or other means of gaining accesss to restricted webpages.

Notifications of page changes are sent via an existing email account. For this purpose,
you must provide login details in the config file, including a plaintext password.

Details of which page URLs to monitor, and how often to check them, are also specified
in the config file.

Required Python libraries:
-Requests
-Beautiful Soup 4

Other requirements:
-Python 3
-If using a Gmail account to send emails, you must allow less secure apps to access the
 account: https://myaccount.google.com/lesssecureapps
"""

from __future__ import print_function
import collections
import configparser
import datetime
import difflib
import os
import smtplib
import time

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from bs4 import BeautifulSoup

SETTINGS_FILE = 'settings.ini'
PAGES_DIR = 'pages'

PROGRAM_SECTION = 'Program'
EMAIL_SERVER_SECTION = 'Email Server'

EMAIL_SUBJECT = 'notify_on_page_change'


class KnownError(Exception):
    pass

class CheckPage(object):
    def __init__(self, page_name, url, check_interval_hours, last_checked):
        self.page_name = page_name
        self.url = url
        self.check_interval_hours = check_interval_hours
        self.last_checked = last_checked

EmailDetails = collections.namedtuple('EmailFormat', ['notify_email_address',
                                                      'email_address',
                                                      'password',
                                                      'smtp_server',
                                                      'port'])


def send_email(email_details, subject, body):
    recipients = [email_details.notify_email_address]

    msg = MIMEText(body.encode('utf-8'), 'plain', 'utf-8')
    msg['From'] = email_details.email_address
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

    try:
        server = smtplib.SMTP_SSL(email_details.smtp_server, email_details.port)
        server.ehlo()
        server.login(email_details.email_address, email_details.password)
        server.send_message(msg)
        server.close()
    except Exception as error:
        print('Unable to send email:', str(error))


def get_readable_page(html):
    soup = BeautifulSoup(html, features='lxml')

    # Remove JavaScript tags from output
    for tag in soup(['script', 'style']):
        tag.decompose()

    readable = soup.get_text()

    # Remove extra blank lines and such
    readable = '\n'.join([line.strip(' ')
                          for line in readable.splitlines()
                          if len(line.strip(' ')) > 0])

    return readable


def check_change(page_name, url, current_time, email_details):
    current_time_str = current_time.strftime('%m/%d/%Y %H:%M:%S')

    try:
        request = requests.get(url)
        new_page_html = request.text
    except Exception:
        message = '{}: {}: Page inaccessible'.format(current_time_str, page_name)
        print(message)
        send_email(email_details, EMAIL_SUBJECT, message)
    else:
        new_page_readable = get_readable_page(new_page_html)

        page_file_path = os.path.join(PAGES_DIR, page_name) + '.html'

        if not os.path.exists(page_file_path):
            message = '{}: {}: Created initial page'.format(current_time_str, page_name)
            print(message)
            send_email(email_details, EMAIL_SUBJECT, message)
        else:
            with open(page_file_path, 'r') as page_input_file:
                old_page_html = page_input_file.read()
                old_page_readable = get_readable_page(old_page_html)

            if old_page_readable == new_page_readable:
                print('{}: {}: No change'.format(current_time_str, page_name))
            else:
                differences = list(difflib.ndiff(old_page_readable.splitlines(),
                                                 new_page_readable.splitlines()))

                readable_difference = '\n'.join(differences)

                message = '{}: {}: Page changed'.format(current_time_str, page_name) + \
                          '\n\nDifferences:' + \
                          '\n--------------------------------\n' + \
                          readable_difference + \
                          '\n--------------------------------\n'

                print(message.encode('utf-8').decode())
                send_email(email_details,
                           EMAIL_SUBJECT,
                           message)

        with open(page_file_path, 'w') as page_output_file:
            page_output_file.write(new_page_html)


def get_config_option(config, section, option):
    try:
        return config[section][option]
    except KeyError:
        raise KnownError('Missing config option: [{}] -> {}'.format(section, option))


def main():
    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE)

    if not os.path.exists(PAGES_DIR):
        os.mkdir(PAGES_DIR)

    notify_email_address = get_config_option(config,
                                             PROGRAM_SECTION,
                                             'notify_email_address')
    server_email_address = get_config_option(config,
                                             EMAIL_SERVER_SECTION,
                                             'email_address')
    server_password = get_config_option(config, EMAIL_SERVER_SECTION, 'password')
    server_smtp_address = get_config_option(config, EMAIL_SERVER_SECTION, 'smtp_server')
    server_port = get_config_option(config, EMAIL_SERVER_SECTION, 'port')

    email_details = EmailDetails(notify_email_address,
                                 server_email_address,
                                 server_password,
                                 server_smtp_address,
                                 int(server_port))

    # Test email server.
    try:
        server = smtplib.SMTP_SSL(email_details.smtp_server, email_details.port)
        server.ehlo()
        server.login(email_details.email_address, email_details.password)
        server.close()
    except Exception as error:
        raise KnownError('Unable to connect to email account: ' + str(error))

    pages_to_check = []

    section_names = config.sections()
    section_names.remove('Program')
    section_names.remove('Email Server')

    if len(section_names) == 0:
        raise KnownError('No page names given in config file')

    for page_name in section_names:
        try:
            url = config[page_name]['url']
        except KeyError:
            raise KnownError('Missing config option: [{}] -> {}'.format(page_name,
                                                                        'url'))

        try:
            check_interval_str = config[page_name]['check_every_x_hours']
        except KeyError:
            raise KnownError('Missing config option: [{}] -> {}'.format(
                page_name, 'check_every_x_hours'))

        try:
            check_interval_hours = int(check_interval_str.rstrip('h'))
            if check_interval_hours < 1:
                raise ValueError
        except ValueError:
            raise KnownError('Invalid value for config option: [{}] -> {}'.format(
                page_name, 'check_every_x_hours'))

        pages_to_check.append(CheckPage(page_name,
                                        url,
                                        check_interval_hours,
                                        None))

    for page in pages_to_check:
        current_time = datetime.datetime.now()
        page.last_checked = current_time
        check_change(page.page_name, page.url, current_time, email_details)

    while True:
        next_page = None
        next_page_time_due = None

        for page in pages_to_check:
            time_due = page.last_checked + datetime.timedelta(
                hours=page.check_interval_hours)
            if next_page_time_due is None or time_due < next_page_time_due:
                next_page = page
                next_page_time_due = time_due

        sleep_seconds = (next_page_time_due - datetime.datetime.now()).total_seconds()
        print('Sleeping for {} seconds before checking {}'.format(round(sleep_seconds),
                                                                  next_page.page_name))

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

        current_time = datetime.datetime.now()
        next_page.last_checked = current_time
        check_change(next_page.page_name, next_page.url, current_time, email_details)


if __name__ == '__main__':
    try:
        main()
    except KnownError as error:
        print(error)

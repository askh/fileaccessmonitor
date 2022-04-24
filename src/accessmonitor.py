#!/usr/bin/env python3

import argparse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
import inotify.adapters
import logging
import os
from smtplib import SMTP
import time
import yaml

DEFAULT_CONFIG_FILE_NAME = 'accessmonitor.yml'

def notify(config, files):
    logging.debug(f"notify for files: {', '.join(files)}")
    content = "Access registered to files:\n" + "\n".join(files)
    conf = config['smtp']
    message = MIMEMultipart()
    message['From'] = conf['from']
    message['To'] = COMMASPACE.join(conf['to'])
    message['Subject'] = conf['subject']
    message['Date'] = formatdate(localtime=True)
    message.attach(MIMEText(content))    
    with SMTP(conf['host']) as smtp:
        smtp.ehlo()
        smtp.sendmail(conf['from'],
                      conf['to'],
                      message.as_string())

def main():
    last_event_time = 0
    items_last_event_time = { }
    unsended = set()
    
    current_dir = os.path.dirname(os.path.realpath(__file__))
    default_config_file = os.path.join(current_dir, DEFAULT_CONFIG_FILE_NAME)
    arg_parser = argparse.ArgumentParser(description='File watcher')
    arg_parser.add_argument('-c',
                            '--config',
                            metavar='CONFIG_FILE',
                            type=str,
                            nargs='?',
                            help='Config file path',
                            default=default_config_file)
    arg_parser.add_argument('-d',
                            '--debug',
                            action='store_true',
                            default=False,
                            help=argparse.SUPPRESS)
    args = arg_parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        
    try:
        with open(args.config, 'r') as conf_file:
            config = yaml.safe_load(conf_file)
    except RuntimeError as e:
        logging.debug(f"Can't load the config file {args.config}. Exception: {e}")
        sys.exit(f"Can't load the config file {args.config}.")

    inf = inotify.adapters.Inotify()
    for file in config["files"]:
        inf.add_watch(file)

    for event in inf.event_gen(yield_nones=False):
        current_time = time.time()
        (_, type_names, path, filename) = event
        full_path = os.path.join(path, filename)
        unsended.add(full_path)
        if (last_event_time == 0 or last_event_time + config['limits']['general_interval'] < current_time) and \
           (full_path not in items_last_event_time.keys() or \
            items_last_event_time[full_path] + config['limits']['item_interval'] < current_time):
            last_event_time = current_time
            items_last_event_time[full_path] = current_time
            notify(config, unsended)
            unsended.clear()

if __name__ == '__main__':
    main()

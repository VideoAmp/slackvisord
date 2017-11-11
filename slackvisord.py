#!/usr/bin/env python
#
# [eventlistener:slackvisord]
# command=python /opt/slackvisord/slackvisord.py
# events=PROCESS_STATE,TICK_60

"""
Usage: slackvisord [-t token] [-c channel] [-n hostname]

Options:
  -h, --help            show this help message and exit
  -t TOKEN, --token=TOKEN
                        Slack Token
  -c CHANNEL, --channel=CHANNEL
                        Slack Channel
  -n HOSTNAME, --hostname=HOSTNAME
                        System Hostname
"""
import os
import sys
import copy
from slacker import Slacker
from superlance.process_state_monitor import ProcessStateMonitor
from supervisor import childutils

class SlackvisorD(ProcessStateMonitor):
    process_state_events = ['PROCESS_STATE_FATAL', 'PROCESS_STATE_EXITED', 'PROCESS_STATE_STARTING', 'PROCESS_STATE_RUNNING', 'PROCESS_STATE_BACKOFF', 'PROCESS_STATE_STOPPING', 'PROCESS_STATE_STOPPED']

    @classmethod
    def _get_opt_parser(cls):
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-t", "--token", help="Slack Token")
        parser.add_option("-c", "--channel", help="Slack Channel")
        parser.add_option("-n", "--hostname", help="System Hostname")
        return parser

    @classmethod
    def parse_cmd_line_options(cls):
        parser = cls._get_opt_parser()
        (options, args) = parser.parse_args()
        return options

    @classmethod
    def validate_cmd_line_options(cls, options):
        parser = cls._get_opt_parser()
        if not options.token:
            parser.print_help()
            sys.exit(1)
        if not options.channel:
            parser.print_help()
            sys.exit(1)
        if not options.hostname:
            import socket
            options.hostname = socket.gethostname()
        validated = copy.copy(options)
        return validated

    @classmethod
    def get_cmd_line_options(cls):
        return cls.validate_cmd_line_options(cls.parse_cmd_line_options())

    @classmethod
    def create_from_cmd_line(cls):
        options = cls.get_cmd_line_options()

        if 'SUPERVISOR_SERVER_URL' not in os.environ:
            sys.stderr.write('Must run as a supervisor event listener\n')
            sys.exit(1)

        return cls(**options.__dict__)

    def __init__(self, **kwargs):
        ProcessStateMonitor.__init__(self, **kwargs)
        self.channel = kwargs.get('channel', None)
        self.token = kwargs.get('token', None)
        self.hostname = kwargs.get('hostname', None)

    def get_process_state_change_msg(self, headers, payload):
        pheaders, pdata = childutils.eventdata(payload + '\n')
        txt = ("[{0}] {groupname}:{processname} - {event}".format(
            self.hostname,
            event=headers['eventname'],
            processname=pheaders['processname'],
            groupname=pheaders['groupname']))
        return txt

    def send_batch_notification(self):
        message = self.get_batch_message()
        if message:
            self.send_message(message)

    def get_batch_message(self):
        return {
            'token': self.token,
            'channel': self.channel,
            'messages': self.batchmsgs
        }

    def send_message(self, message):
        for msg in message['messages']:
            alert_color = 'danger';
            if 'PROCESS_STATE_STARTING' in msg:
                alert_color = "warning"
            if 'PROCESS_STATE_RUNNING' in msg:
                alert_color = "good"
            payload = {
                'channel': self.channel,
                'attachments': [{"text": msg, "color": alert_color}]
            }
            slack = Slacker(self.token)
            slack.chat.post_message(**payload)

def main():
    slackvisord = SlackvisorD.create_from_cmd_line()
    slackvisord.run()

if __name__ == '__main__':
    main()

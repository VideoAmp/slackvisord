# slackvisord
SupervisorD event listener for Slack

# Installation
* Generate a [Slack Bot User](https://api.slack.com/bot-users) (you will need a bot user token for the supervisord command below)
* Copy the conf example below to your supervisord.conf file (use absolute path to the slackvisord.py provided here)

## supervisord.conf Example:
```
[eventlistener:slackvisord]
command=/usr/bin/python /opt/slackvisord/slackvisord.py -t "{slack bot token here (starts with xoxb-)}" -c "#some-channel"
events=PROCESS_STATE,TICK_60
```

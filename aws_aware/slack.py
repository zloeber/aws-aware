"""
Slack integration
"""
from __future__ import absolute_import

import requests

try:
    # Import as part of the aws_aware project
    from aws_aware.outputclass import OUTPUT
except ImportError:
    # Otherwise import locally and define out ouput stream manually
    from outputclass import Output as outstream
    OUTPUT = outstream()


class SlackPoster(object):
    """
    Class for posting slack messages via json formatted webhook requests
    """

    def __init__(self, webhooks):
        self.webhooks = webhooks

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))

    def post_message(self, slack_data):
        """Accepts dictionary of slack attachment data and posts it to the webhooks"""
        for webhook in self.webhooks:
            response = requests.post(webhook, json=slack_data)
            if response.status_code != 200:
                self._add_log('Request to slack returned an error {0}, the response is: {1}'.format(response.status_code, response.text), logtype='error')
                raise ValueError(
                    'Request to slack returned an error {0}, the response is: {1}'.format(response.status_code, response.text)
                )


if __name__ == "__main__":
    """
    slack_webhooks = 'https://hooks.slack.com/services/<rest of url>'
    slk = SlackPoster(slack_webhooks)
    clusterinfo = [
        {
            "title": "Lifecycle ID",
            "value": "123456789",
            "short": True
        },
        {
            "title": "Cluster Name",
            "value": "team2s-dev-subteam-a3",
            "short": True
        },
        {
            "title": "Gateway IP",
            "value": "Unknown",
            "short": True
        }
    ]
    emrSlackNoticeTemplate = {
        "attachments": [
            {
                "fallback": "EMR Build - In Progress",
                "text": "EMR Build - In Progress",
                "color": "warning",
                "fields": []
            }
        ]
    }
    emrSlackNotices = {
        "inprogress": {
            "attachments": [
                {
                    "fallback": "EMR Build - In Progress",
                    "text": "EMR Build - In Progress",
                    "color": "warning",
                    "fields": []
                }
            ]
        },
        'buildcomplete': {
            "attachments": [
                {
                    "fallback": "EMR Build - Build Complete",
                    "text": "EMR Build - Build Complete",
                    "color": "good",
                    "fields": [
                        {
                            "title": "Lifecycle ID",
                            "value": "123456789",
                            "short": True
                        },
                        {
                            "title": "Cluster Name",
                            "value": "team2-dev-subteam-B8",
                            "short": True
                        },
                        {
                            "title": "Gateway IP",
                            "value": "10.237.189.143",
                            "short": True
                        }
                    ]
                }
            ]
        }
    }

    #emrSlackNotices['buildcomplete']['attachments'][0]['fields'] = clusterinfo

    EMRInProgress = emrSlackNoticeTemplate.copy()
    EMRInProgress['attachments'][0]['fields'] = clusterinfo
    EMRInProgress['attachments'][0]['fallback'] = 'EMR Build - In Progress'
    EMRInProgress['attachments'][0]['text'] = 'EMR Build - In Progress'
    EMRInProgress['attachments'][0]['color'] = 'warning'

    slk.post_message(EMRInProgress)
    """
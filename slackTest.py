from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = 'xoxb-2904724697475-2901783823621-W3nHJbxA3d4ajowkPZfuObzz'

client = WebClient(token=slack_token)


mrkdwn_text = '''
This is test message.
> Block quote

*Bold text*

```
code block - line 1
code block - line 2\ncode block - line 3
```

`highlight`

_italicize_

~Strikethrough~

<https://www.google.com|This is link to google.com>
'''


try:
    response = client.chat_postMessage(channel='#crypto',
                                       text=mrkdwn_text)
    print(response.status_code)
except SlackApiError as e:
    print('Error: {}'.format(e.response['error']))
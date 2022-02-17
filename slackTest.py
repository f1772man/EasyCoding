from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = 'xoxb-2904724697475-2901783823621-9BpFVVf3rFKm92gC235KBEq5'

client = WebClient(token=slack_token)


mrkdwn_text = '''
```
>08:50 AM```
`CVC`
```▲-7.4%
376.0원
10분봉 5MA: 매수```
`DOGE`
```▲-2.2%
182.0원
10분봉 5MA: 매수```
`NU`
```▲-10.5%
670.0원
10분봉 5MA: 매수```
`FLOW`
```▼-12.2%
8910.0원
10분봉 5MA: 매도```
'''


try:
    response = client.chat_postMessage(channel='#crypto',
                                       text=mrkdwn_text)
    print(response.status_code)
except SlackApiError as e:
    print('Error: {}'.format(e.response['error']))
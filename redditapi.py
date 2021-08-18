import requests


class Reddit:
    '''
    Constructor for the reddit API
    '''

    def __init__(self):
        return

    '''
    Function calls reddit api to get the free deals of the hottest
    returns a string.'''

    def getHotdeals(self):
        Client_ID = 'Redacted'
        SECRET_ID = 'Redacted'

        # The authenticator for requests
        auth = requests.auth.HTTPBasicAuth(Client_ID, SECRET_ID)

        # The dic we give to log in
        data = {
            'grant_type': 'password',
            'username': 'REDACTED',
            'password': 'REDACTED'
        }

        headers = {'User-Agent': "Version 0.1"}

        # Send request
        req = requests.post('https://www.reddit.com/api/v1/access_token', \
                            auth=auth, data=data, headers=headers)

        # The Token
        TOKEN = (req.json())['access_token']
        headers['Authorization'] = f'bearer {TOKEN}'

        deals = []
        # The request of the hottest post.
        req = requests.get('https://oauth.reddit.com/r/GameDeals/hot',
                           headers=headers)

        for post in req.json()['data']['children']:

            if (post['data']['title'].lower().find("free") != -1 and
                    post['data']['title'].find("100") != -1):
                if (post['data'][
                    'link_flair_css_class']) != 'expired':  # if the deal is expired, dont post it

                    lst = post['data']['title'] + '\n' + post['data']['url']
                    deals.append(lst)

        return deals

from chef import api
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings
import six.moves.urllib.parse


disable_warnings(InsecureRequestWarning)


class ChefAPI:

    def __init__(self):
        self.data_path = Path('data/')
        self.auth()

    def auth(self):
        pem = str(self.data_path / 'odtwapa.pem')
        self.chef_server = api.ChefAPI(
            'https://chef.dti.state.de.us/organizations/dti', pem,
            'odtwapa',
            ssl_verify=False)

    def chef_get(self, end_point, node=''):
        self.end_point = end_point + node
        response = self.chef_server.api_request('GET', self.end_point)
        return response

    def chef_post(self):
        pass

    def chef_search(self, index=None, query=None, header={}):
        if query is None and index is None:
            self.search = '/search'
        elif query is None:
            self.search = '/search/' + index
        elif index is None:
            print("Please provide an index with your query.")
            self.search = '/search'
        else:
            self.query = dict(q=query, rows=1000, start=0)
            self.search = ('/search/'
                           + index
                           + '?'
                           + six.moves.urllib.parse.urlencode(self.query))
        response = self.chef_server.api_request('GET', self.search, header)
        return response

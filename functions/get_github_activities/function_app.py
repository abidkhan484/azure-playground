import azure.functions as func
import logging
from os import getenv
from requests import get
from json import loads, dumps

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def get_github_activities(username: str) -> list:
    url = f'https://api.github.com/users/{username}/events/public'
    api_res = get(url)
    logging.info(f'Github public event retrieval url is {url}')

    if api_res.status_code == 200:
        output = []
        api_response = loads(api_res.text)
        for event in api_response:
            output_dict = {
                'type': event['type'],
                'repo': {
                  'name': event['repo']['name'],
                  'url': event['repo']['url'],
                },
                'action': event['payload'].get('action', None),
            }
            output.append(output_dict)
        response = dumps(output)
        logging.info(f'Final output of user {username} is {response}')
        return output
    else:
        logging.error(f'Got an error response from the GITHUB API where status code {api_res.status_code}.')
        return []

@app.route(route='activity/github')
def github_activites(req: func.HttpRequest) -> func.HttpResponse:
    username = req.params.get('username') if req.params.get('username') else getenv('GITHUB_USERNAME')
    if not username:
        return func.HttpResponse(
             'Username not found',
             status_code=404
        )

    output = get_github_activities(username)
    if output:
        response = dumps(output)
        logging.info(f'Final output of user {username} is {response}')
        return func.HttpResponse(response)
    else:
        return func.HttpResponse(
             'Got an error response from the GITHUB API.',
             status_code=200
        )

######################################################

def store_github_activities_in_db() -> bool:
    pass

######################################################
from cassandra.cluster import Cluster
from ssl import PROTOCOL_TLSv1_2, SSLContext, CERT_NONE
from cassandra.auth import PlainTextAuthProvider

@app.route(route='connect/db', auth_level=func.AuthLevel.FUNCTION)
def connect_with_db(req: func.HttpRequest) -> func.HttpResponse:
    username = getenv('CASSANDRA_USERNAME')
    password = getenv('CASSANDRA_PASSWORD')
    domain = getenv('CASSANDRA_DOMAIN')
    keyspace = getenv('CASSANDRA_KEYSPACE')

    ssl_context = SSLContext(PROTOCOL_TLSv1_2)
    ssl_context.verify_mode = CERT_NONE

    auth_provider = PlainTextAuthProvider(username=username, password=password)
    cluster = Cluster([domain], port = 10350, auth_provider=auth_provider, ssl_context=ssl_context)
    session = cluster.connect(keyspace)

    if session:
        cluster.shutdown()
        session.shutdown()
        return func.HttpResponse('Cassandra session created succesfully.')
    else:
        return func.HttpResponse(
             'Cassandra session error.',
             status_code=200
        )

######################################################



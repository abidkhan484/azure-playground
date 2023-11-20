import azure.functions as func
import logging
from os import getenv
from requests import get
from json import loads, dumps

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="request/github")
def github_request(req: func.HttpRequest) -> func.HttpResponse:
    username = getenv('GITHUB_USERNAME')
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
        return func.HttpResponse(response)
    else:
        return func.HttpResponse(
             "Got an error response from the GITHUB API.",
             status_code=200
        )


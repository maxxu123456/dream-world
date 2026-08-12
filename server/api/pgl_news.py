import json

# ---------------------
# GET API calls
# ---------------------

def GET_information_list(_query):
    response = {"list":[], "total_count":0}
    return json.dumps(response).encode()


def GET_news_list(_query):
    print(json.dumps(_query, indent=2))
    return b'{}'

# ---------------------
# POST API calls
# ---------------------

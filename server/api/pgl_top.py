import json

from utils import text
from utils import language
from utils import save_data

# ---------------------
# GET API calls
# ---------------------

def GET_index(_query):
    response = {
        "stats": {
            "pgl_population": 1
        }
    }
    return json.dumps(response).encode()


def GET_init(_query):
    response = save_data.read_player_data()

    response["member"].update({
        "pokemon_name": text.lookup_str("pokemon", response["member"]["pokemon_no"]),
        "rom_name": text.lookup_str("game", response["member"]["rom_id"]),
        "last_up_time": language.localize_last_up_time(response["member"]["last_started_at_timezone"])
    })

    return json.dumps(response).encode()

# ---------------------
# POST API calls
# ---------------------

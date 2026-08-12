import json

from utils import managers

# ---------------------
# GET API calls
# ---------------------

def GET_my_croft_list(_query):
    return(json.dumps(managers.crops.data).encode())


def GET_tutorial_end(_query):
    return b'{}'


def GET_tutorial_start(_query):
    return b'{}'


def GET_waterpot_list(_query):
    response = {
        "waterpot_list": [
            {
            "my_interior_id": 283,
            "interior_id": 1,
            "selected_flag": 1,
            "interior_name": "ふつうのじょうろ"
            },
            {
            "my_interior_id": 284,
            "interior_id": 2,
            "selected_flag": 0,
            "interior_name": "ふつうのじょうろ"
            }
        ]
    }

    return json.dumps(response).encode()

# ---------------------
# POST API calls
# ---------------------

def POST_kinomi_harvesting(_query):
    my_croft_id = int(_query.get("my_croft_id"))

    harvest_result = managers.crops.harvest(my_croft_id)
    managers.chest.add_item(harvest_result["pokeitem_id"], harvest_result["count"])

    return json.dumps(harvest_result).encode()


def POST_kinomi_sowing(_query):
    my_croft_id = int(_query.get("my_croft_id"))
    pokeitem_id = int(_query.get("pokeitem_id"))

    managers.crops.sow(my_croft_id, pokeitem_id)
    managers.chest.remove_item(pokeitem_id, 1)

    return json.dumps(managers.crops.data).encode()


def POST_kinomi_watering(_query):
    my_croft_id = int(_query.get("my_croft_id"))

    managers.crops.water_plot(my_croft_id)

    return json.dumps(managers.crops.data).encode()


def POST_waterpot_list(_query):
    response = {
        "waterpot_list": [
            {
            "my_interior_id": 283,
            "interior_id": 1,
            "selected_flag": 1,
            "interior_name": "Watering Can"
            }
        ]
    }
    return json.dumps(response).encode()
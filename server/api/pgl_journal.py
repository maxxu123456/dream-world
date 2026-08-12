import json

# ---------------------
# GET API calls
# ---------------------

def GET_census(_query):
    result = {"census_list":[]}
    
    # Dummy data
    gts_census = {
        "lead": "Top GTS Locations", # Type of leaderboard (new chore: find all types)
        "ranking_list": [
            {
                "ranking": 1, # Ranking showed in the circle
                "country_id": 176, # PGL country id
                "pokemon_no": 494, # Most tucked-in Pokémon in this area
                "label": "Avg. 100 times" # Numbers are automatically formatted
            },
            {
                "ranking": 2,
                "country_id": 60,
                "pokemon_no": 517,
                "label": "Avg. 50 times"
            }
        ]
    }
    
    result["census_list"].append(gts_census)
    return json.dumps(result).encode()

# ---------------------
# POST API calls
# ---------------------

import json

from utils import language
from utils import save_data

def build_swf_params() -> dict:
    player_data = save_data.read_player_data()
    return {
        "json": json.dumps({
            "member": player_data["member"],
            "token":  player_data.get("token", ""),
            "medals": player_data.get("medals", []),
        }),
        "v":             "2.0",
        "api_host_name": "/api/",
        "page":          "SITE_PDW",
        "lang":          language.player_language+".",
    }
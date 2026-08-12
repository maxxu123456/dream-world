from pathlib import Path

from utils import language

ROOT_DIR = Path(__file__).resolve().parent.parent

def lookup_str(str_type: str, index: int):
    if str_type == "game":
        index -= 20

    try:
        return raw_text[language.player_language][str_type][index]

    except KeyError:
        return None

raw_text = {k: {} for k in language.lang_index.values()}
for folder in (ROOT_DIR / "raw_text").iterdir():
    for file in folder.iterdir():
        with open(ROOT_DIR / "raw_text" / folder.stem / file, "r", encoding="UTF-8") as f:
            strings = f.read().splitlines()

        if file.stem.endswith("_descriptions"):
            raw_text[folder.stem][file.stem] = {}

            for i, val in enumerate(strings):
                string = val.split("\\n")
                res = [None, None, None]
                res[:len(string)] = string

                raw_text[folder.stem][file.stem][i] = res

        else:
            raw_text[folder.stem][file.stem] = {i: val for i, val in enumerate(strings)}
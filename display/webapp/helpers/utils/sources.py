import json
import os

from display.webapp.config import Config

config = Config()


def get_display_sources():
    try:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "r") as f:
            config_json = json.loads(f.read())

        display_sources = config_json

    except FileNotFoundError:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "w") as f:
            f.write(json.dumps({"none": [{}]}))

        display_sources = {"none": [{}]}

    return display_sources


def chunks(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def get_display_source_chunk(number=0, chunk_size=1):

    ds = get_display_sources()

    chunk_list = list(chunks(list(ds.keys()), chunk_size))

    ret_data = {}

    if number >= len(chunk_list):
        number = len(chunk_list) - 1

    for each in chunk_list[number]:
        ret_data[each] = ds[each]

    return ret_data

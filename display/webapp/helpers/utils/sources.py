import collections
import json
import os

from display.webapp.config import Config

config = Config()


def get_display_sources(add_header_tabs: bool = False):
    try:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "r") as f:
            config_json = json.loads(f.read())

        display_sources = config_json

    except FileNotFoundError:
        with open(os.path.join(config.CONFIG_PATH, config.CONFIG_FILE), "w") as f:
            f.write(json.dumps({"none": [{}]}))

        display_sources = {"none": [{}]}

    if add_header_tabs:
        header_display_sources = add_header_tabs_from_sources(display_sources)

        display_sources = {**display_sources, **header_display_sources}

    # let's order the entries....
    ordered_dict = collections.OrderedDict()

    for each in sorted(list(display_sources.keys())):
        ordered_dict[each] = display_sources[each]

    display_sources = dict(ordered_dict)

    return display_sources


def add_header_tabs_from_sources(sources):

    ret_dict = collections.defaultdict(list)

    for target, urls in sources.items():
        for url_entry in urls:
            ret_dict[url_entry['header']].append(url_entry)

    return dict(ret_dict)


def get_screenshot_sources():
    try:
        with open(
            os.path.join(config.CONFIG_PATH, config.SCREENSHOT_SOURCE_CONFIG_FILE), "r"
        ) as f:
            screenshot_config_json = json.loads(f.read())

        screenshot_sources = screenshot_config_json

    except FileNotFoundError:
        with open(
            os.path.join(config.CONFIG_PATH, config.SCREENSHOT_SOURCE_CONFIG_FILE), "w"
        ) as f:
            f.write(json.dumps({"none": ["none"]}))

        screenshot_sources = {"none": ["none"]}

    return screenshot_sources


def chunks(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))


def get_display_source_chunk(number=0, chunk_size=1):
    ds = get_display_sources()

    chunk_list = list(chunks(list(ds.keys()), chunk_size))

    ret_data = {}

    if number >= len(chunk_list):
        number = len(chunk_list) - 1

    for each in chunk_list[number]:
        ret_data[each] = ds[each]

    return ret_data

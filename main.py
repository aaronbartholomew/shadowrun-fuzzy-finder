import argparse
import glob
import json
import os
import random
import xmltodict
from fuzzywuzzy import process
from pygments import highlight, lexers, formatters

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR_CHUMMER = os.path.join(ROOT_DIR, 'data')
DATA_FILE_PROCESSED = os.path.join(ROOT_DIR, 'sr5_data.json')
DATA_FILE_FLATTENED = os.path.join(ROOT_DIR, 'sr5_data_flat.json')


def hprint(j_data):
    """ Utility function to print formatted + highlighted JSON to
    console

    Args:
        j_data (dict): The json to print

    """
    if not isinstance(j_data, dict):
        raise Exception('trying to print a non-json object', type(j_data))

    formatted_json = json.dumps(j_data, sort_keys=True, indent=4)
    colorful_json = highlight(formatted_json, lexers.JsonLexer(), formatters.Terminal256Formatter())
    print(colorful_json)


def process_chummer_data(chummer_data_dir, dst_json_file):
    """ Extract the relevant content from Chummer XML
    and dump it to a more palatable json

    Args:
        chummer_data_dir (str): The dir that contains all the Chummer XML
        dst_json_file (str): Path to write the procssed json to disk

    """
    if not os.path.exists(chummer_data_dir):
        raise Exception('data dir does not exist:', chummer_data_dir)

    skip_keys = [
        '@xmlns',
        '@xmlns:xsi',
        '@xsi:schemaLocation',
        'categories',
        'modcategories',
        'version'
    ]
    out_json = {}

    files = glob.glob(chummer_data_dir + os.path.sep + '*.xml')
    for f in files:
        with open(f) as f_xml:
            xml = f_xml.read()
        print('Processing FILE:', os.path.basename(f))
        j_data = xmltodict.parse(xml)['chummer']
        out_root_k = os.path.basename(f).split('.')[0]
        out_json[out_root_k] = {}

        for k,v in j_data.items():
            if k in skip_keys:
                continue
            if k not in out_json[out_root_k]:
                out_json[out_root_k] = {}

            if not isinstance(j_data[k], dict):
                continue

            for s_k,s_v in j_data[k].items():
                if not isinstance(s_v, list) or len(s_k) < 1:
                    continue

                # check type
                if isinstance(s_v[0], dict):
                    out_json[out_root_k] = {}
                else:
                    out_json[out_root_k] = []

                for item in s_v:
                    if isinstance(item, dict):
                        if 'name' not in item:
                            if 'category' in item:
                                out_json[out_root_k][item['category']] = item
                        else:
                            out_json[out_root_k][item['name']] = item
                    else:
                        out_json[out_root_k].append(item)
        print('================================================================================')

    with open(dst_json_file, 'w') as f:
        json.dump(out_json, f)


def flatten_processed_data(src_json_file, dst_json_file):
    """ Takes json generated from Chummer XML & flattens the entries
    to be queryable

    Args:
        src_json_file (str): The Chummer XML -> JSON file
        dst_json_file (str): Path to write the flattened json to disk

    """
    if not os.path.exists(src_json_file):
        raise Exception('src json does not exist:', src_json_file)

    out_json = {}
    with open(src_json_file, 'r') as f:
        j_data = json.load(f)

    for k,v in j_data.items():
        print('flattening:', k)
        if isinstance(v, dict):
            for s_k, s_v in v.items():
                out_json[s_k] = s_v

    with open(dst_json_file, 'w') as f:
        json.dump(out_json, f)


def inspect_processed_data(data_json_file, count=10):
    """ Print some random values from flat json file to console

    Args:
        data_json_file (str): The source json file
        count (int): How many random values to print

    """
    if not os.path.exists(data_json_file):
        raise Exception('src json does not exist:', data_json_file)

    with open(data_json_file, 'r') as f:
        j_data = json.load(f)

    print('inspecting', count, 'random items')
    print('from:', data_json_file)

    l_keys = list(j_data.keys())
    keys = [random.choice(l_keys) for i in range(count)]
    out = {}
    for k in keys:
        out[k] = j_data[k]
    hprint(out)


def query_data(query_text, key_list, j_db, max_results=5):
    """ Extract closest matching N entries from json object
    and prints formatted key/value to console; sorted by closest
    matching.  Query is compared against key value

    Args:
        query_text (str): The key to search for
        key_list (list): Preprocessed list of all keys in the json object, used for pattern matching
        j_db (dict): The dict to pull the data for matching keys from

    """
    SOURCE_TO_BOOK = {
        "SHB2"	:	"Schattenhandbuch 2 (German Handbook)",
        "BB"	:	"Bullets & Bandages",
        "HS"	:	"Howling Shadows",
        "HT"	:	"Hard Targets",
        "DTD"	:	"Data Trails (Dissonant Echoes)",
        "FA"	:	"Forbidden Arcana",
        "DT"	:	"Data Trails",
        "2050"	:	"Shadowrun 2050 (5th Edition)",
        "BOTL"	:	"Book of the Lost",
        "SASS"	:	"Sail Away, Sweet Sister",
        "HKS"	:	"Hong Kong Sourcebook",
        "TCT"	:	"The Complete Trog",
        "SPS"	:	"Splintered State",
        "SAG"	:	"State of the Art ADL (German Handbook)",
        "RF"	:	"Run Faster",
        "RG"	:	"Run & Gun",
        "SR4"	:	"Shadowrun, Fourth Edition",
        "SR5"	:	"Shadowrun, Fifth Edition",
        "TVG"	:	"The Vladivostok Gauntlet",
        "SGG"	:	"Street Grimoire (German-exclusive Content)",
        "R5"	:	"Rigger 5.0",
        "CA"	:	"Cutting Aces",
        "CF"	:	"Chrome Flesh",
        "AP"	:	"Assassin's Primer",
        "WAR"	:	"WAR!",
        "GH3"	:	"Gun Heaven 3",
        "SS"	:	"Stolen Souls",
        "SFB"	:	"Shadows In Focus: Butte",
        "SSP"	:	"Shadow Spells",
        "LCD"	:	"Lockdown",
        "SG"	:	"Street Grimoire",
    }

    found = process.extract(query_text, key_list, limit=max_results)
    for i,f in enumerate(found):
        entry  = j_db[f[0]]
        print('================================================================================')
        print(i+1, ':', f)
        if 'page' in entry and 'source' in entry:
            if  entry['source'] in SOURCE_TO_BOOK:
                src = SOURCE_TO_BOOK[entry['source']]
            else:
                src = entry['source']

            print('NAME', f[0])
            print('BOOK:', src)
            print('PAGE:', entry['page'])
        hprint(entry)
        print('================================================================================')
    print('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['process', 'flatten', 'inspect', 'query'])
    parser.add_argument('--max-results', type=int, default=5, help='how many results to return from query')
    args = parser.parse_args()

    if args.action == 'process':
        process_chummer_data(DATA_DIR_CHUMMER, DATA_FILE_PROCESSED)
    elif args.action == 'flatten':
        flatten_processed_data(DATA_FILE_PROCESSED, DATA_FILE_FLATTENED)
    elif args.action == 'inspect':
        inspect_processed_data(DATA_FILE_FLATTENED)
    elif args.action == 'query':
        with open(DATA_FILE_FLATTENED, 'r') as f:
            j_data = json.load(f)
        l_keys = list(j_data.keys())
        while True:
            user_input = input(':')
            if len(user_input) == 1:
                # must have at least 2 chars to search
                break
            query_data(user_input, l_keys, j_data, args.max_results)

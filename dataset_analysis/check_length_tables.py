from itertools import repeat
import json
from typing import Iterator
from LLmsfJiT import config, connect, read_trec_queries, read_trec_qrels, remove_empty_cols, remove_empty_rows
import tiktoken


def main():

    qrels = read_trec_qrels("../rel_files/")

    # Insert into tables table, table_meta, text_before, text_after, table_entities
    json_it = read_jsonl("../web_tables.json")

    dropped_tables = 0
    kept_tables = 0

    enc = tiktoken.encoding_for_model("gpt-3.5-turbo-1106")

    for idx, table_json in enumerate(json_it, start=1):
        table = extract_values(table_json)

        # Check length of input 
        if len(enc.encode(table[2])) > (16385): # 100 reserved for other words in query 
            dropped_tables += 1
        else:
            kept_tables += 1

    print(f"Tables total: {dropped_tables + kept_tables}")
    print(f"Tables dropped: {dropped_tables}")
    print(f"Tables kept: {kept_tables}")




def read_jsonl(fn: str) -> Iterator[dict]:
    with open(fn, "r") as fp:
        line = fp.readline()
        continue_reading = True
        while continue_reading:
            line = fp.readline()
            if line == "":
                continue_reading = False
                continue
            try:
                js = json.loads(line)
                yield js
            except json.JSONDecodeError as ex:
                print(f"Error when decoding JSON: {line}")
                continue
 
def extract_values(table_json: dict):

    remove_empty_rows(table_json["relation"])
    remove_empty_cols(table_json["relation"])

    table = (
        table_json["json_loc"],
        table_json["title"],
        json.dumps(table_json["relation"]),
        table_json["tableType"]
        )
    return table

if __name__ == '__main__':
    main()
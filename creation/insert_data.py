from itertools import repeat
import json
from typing import Iterator
from LLmsfJiT import config, connect, read_trec_queries, read_trec_qrels, remove_empty_cols, remove_empty_rows
import tiktoken

BATCH_SIZE = 10000

def main():

    global BATCH_SIZE
    params = config()
    conn, cur = connect(params["postgres"]) 
    db_schema = load_db_schema("schema.sql")

    # Create the db schema
    cur.execute(db_schema)
    conn.commit() 

    # Insert into tables table, table_meta, text_before, text_after, table_entities
    json_it = read_jsonl("web_tables.json")

    table_list = []
    table_meta_list = []
    text_before_list = []
    text_after_list = []
    table_entities_list = []
    page_title_list = []

    removed_tables = set()

    enc = tiktoken.encoding_for_model("gpt-3.5-turbo-0613")

    for idx, table_json in enumerate(json_it, start=1):
        table_extracted = extract_values(table_json)
        table = table_extracted[0]

        # Check length of input 
        if len(enc.encode(table[2])) > (16385 - 100): # 100 reserved for other words in query 
            removed_tables.add(table[0])
            continue 
        table_list.append(table) 
        table_meta_list.append(table_extracted[1])
        text_before_list.append(table_extracted[2])
        text_after_list.append(table_extracted[3])
        table_entities_list.append(table_extracted[4])
        page_title_list.append(table_extracted[5])
        
        if idx % BATCH_SIZE == 0:
            print("inserted Batch")
            batch_insert(cur, "web_table", table_list)
            batch_insert(cur, "table_meta", table_meta_list)
            batch_insert(cur, "text_before", text_before_list)
            batch_insert(cur, "text_after", text_after_list)
            batch_insert(cur, "table_entities", table_entities_list)
            batch_insert(cur, "page_title", page_title_list)
            table_list.clear()
            table_meta_list.clear()
            text_before_list.clear()
            text_after_list.clear()
            table_entities_list.clear() 
            page_title_list.clear()
            conn.commit()
        
    print(f"Finished inserting tables, {len(removed_tables)} skipped due to token length greater then 16285.")

    # insert into table trec_queries
    queries = read_trec_queries("rel_files/queries.txt")
    for qid, query in queries.items():
        cur.execute(f"INSERT INTO queries VALUES ({qid}, '{query}')")
    conn.commit()

    # insert into table trec_qrels
    qrels = read_trec_qrels("rel_files/rel_table_qrels.txt")
    for topic, it, doc, rel in qrels:
        if doc in removed_tables:
            continue
        cur.execute("INSERT INTO qrels VALUES (%s, %s, %s, %s)", (topic, it, doc, int(float(rel))))
    conn.commit()

    # insert into table qrels_entities
    qrels_entity = read_trec_qrels("rel_files/rel_entity_qrels.txt")
    for topic, it, doc, rel in qrels_entity:
        if doc in removed_tables:
            continue
        cur.execute("INSERT INTO qrels_entities VALUES (%s, %s, %s, %s)", (topic, it, doc, int(float(rel))))
    conn.commit()

    qrels_pt = read_trec_qrels("rel_files/rel_PageTitle_qrels.txt")
    for topic, it, doc, rel in qrels_pt:
        if doc in removed_tables:
            continue
        cur.execute("INSERT INTO qrels_page_title VALUES (%s, %s, %s, %s)", (topic, it, doc, int(float(rel))))
    conn.commit()

    qrels_ta = read_trec_qrels("rel_files/rel_textAfter_qrels.txt")
    for topic, it, doc, rel in qrels_ta:
        if doc in removed_tables:
            continue
        cur.execute("INSERT INTO qrels_text_after VALUES (%s, %s, %s, %s)", (topic, it, doc, int(float(rel))))
    conn.commit()

    qrels_tb = read_trec_qrels("rel_files/rel_textBefore_qrels.txt")
    for topic, it, doc, rel in qrels_tb:
        if doc in removed_tables:
            continue
        cur.execute("INSERT INTO qrels_text_before VALUES (%s, %s, %s, %s)", (topic, it, doc, int(float(rel))))
    conn.commit()

    cur.close()
    conn.close()
 



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
        
def load_db_schema(fn: str = "schmema.sql") -> str:
    with open(fn, "r") as fp:
        return fp.read()


def extract_values(table_json: dict):

    remove_empty_rows(table_json["relation"])
    remove_empty_cols(table_json["relation"])

    table = (
        table_json["json_loc"],
        table_json["title"],
        json.dumps(table_json["relation"]),
        table_json["tableType"]
        )

    table_meta =  (
        table_json["json_loc"],
        table_json["hasKeyColumn"],
        table_json["keyColumnIndex"],
        table_json["hasHeader"],
        table_json["headerPosition"],
        table_json["headerRowIndex"],
        table_json["tableOrientation"],
        table_json["tableNum"],
        table_json["recordEndOffset"],
        table_json["recordOffset"],
    )

    text_before = (
        table_json["json_loc"],
        table_json["textBeforeTable"],
    )
    
    text_after = (
        table_json["json_loc"],
        table_json["textAfterTable"],
    )

    table_entities = (
        table_json["json_loc"],
        json.dumps(table_json["entities"])
    )

    page_title = (
        table_json["json_loc"],
        table_json["pageTitle"]
    )

    return table, table_meta, text_before, text_after, table_entities, page_title

def batch_insert(cur, table_name: str, data: list[tuple]):
    """
    Code from https://www.geeksforgeeks.org/python-psycopg2-insert-multiple-rows-with-one-query/"""
    s_chained = ",".join(repeat("%s", len(data[0])))    
    args_texts = []
    for i in data:
        i_clean = i_clean = [x.replace("\x00", "") if isinstance(x, str) else x for x in i] 
        args_texts.append(cur.mogrify(f"({s_chained})", i_clean).decode('utf-8'))
    args = ",".join(args_texts)

    cur.execute(f"""INSERT INTO "{table_name}" VALUES """ + (args))

if __name__ == '__main__':
    print("started")
    main()
    #print(next(read_jsonl("web_tables.json")))
import psycopg2
from LLmsfJiT import config, connect, get_tables_from_qrels, send_plain_request, RatedTable, Table, remove_empty_rows, remove_empty_cols, load_client
import pandas as pd
import re
from random import shuffle, sample
import json
import tiktoken

params = config("../database.ini")
load_client(params["openai"]["apikey"])
conn, cur = connect(params["postgres"])

def generate_qrels(system_instructions: str, fn: str):
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")
    human_rated_tables = get_tables_from_qrels(conn, cur, "../rel_files/rel_table_qrels_sample_100.txt")
    assert len(human_rated_tables) == 100, "length of qrels_file and tables not matching"
    fp = open(fn, "a")


    for idx, hr_table in enumerate(human_rated_tables):
        system_instructions_sub = re.sub(r"\$TOPIC", hr_table.query, system_instructions) 
        table_str = json.dumps(hr_table.table.relation).encode('unicode-escape').decode()
        instruction = re.sub(r"\$TABLE", table_str, system_instructions_sub)
        
        instruction_encoded = enc.encode(instruction)
        if len(instruction_encoded) >= 16385:
            print(f"Cut table with length {len(instruction)}")
            instruction = enc.decode(instruction_encoded[:16385 - 15])

        try:
            response = send_plain_request(instruction)
            rating = None
            if response == "Irrelevant (0)":
                rating = 0
            if response == "Relevant (1)":
                rating = 1
            if rating == None:
                print("Error Response: ", response)
                continue
            else:
                    rt = RatedTable(
                        annotator="gpt-3.5-turbo-16k",
                        query=hr_table.query,
                        query_id=hr_table.query_id,
                        relevancy=rating,
                        table=hr_table.table,
                    )
                    rt.append_to_qrels(fp, 0)
                
        except Exception as ex:
            print("Error Request: ", ex, instruction)
            continue
    fp.close()


if __name__ == '__main__':
    
    system_instructions = """
        You are an expert assessor making relevance judgments on the topic of '$TOPIC'. You will be given a table from a web page. 
        If this table provides no information about '$TOPIC' (i.e., based on the context you would not expect this to be shown as a result from a search engine), answer “Irrelevant (0)”
        If this table provides relevant information about '$TOPIC' (i.e., you would expect this Web page to be included in the search results from a search engine), answer “Relevant (1)”.    
        Table: ```
        $TABLE
        ```
        Relevant?
        """ 
    generate_qrels(system_instructions, "../gpt_judgements/ex_qrels_bin_topic.txt")
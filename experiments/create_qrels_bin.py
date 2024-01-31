import psycopg2
from LLmsfJiT import config, connect, get_tables_from_qrels, send_plain_request, RatedTable, Table, remove_empty_rows, remove_empty_cols, load_client
import tiktoken
import pandas as pd
import re
from random import shuffle, sample
import json

params = config("../database.ini")
load_client(params["openai"]["apikey"])
conn, cur = connect(params["postgres"])

def generate_qrels(instruction_template: str, fn: str, fn_err: str):
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")
    human_rated_tables = get_tables_from_qrels(conn, cur, "../rel_files/rel_table_qrels.txt")
    fp = open(fn, "a")
    fp_err = open(fn_err, "a")
    
    for idx, hr_table in enumerate(human_rated_tables, start=1):
        request_succeeded = False
        request_counter = 0
        while request_succeeded != True: 


            instruction = re.sub(r"\$TOPIC", hr_table.query, instruction_template) 
            table_str = json.dumps(hr_table.table.relation).encode('unicode-escape').decode()    

            instruction = instruction.replace(r"$TABLE", table_str)
            # re.sub(r"\$TABLE", table_str, instruction)

            instruction_encoded = enc.encode(instruction)
            if len(instruction_encoded) >= 16385:
                print(f"Cut table with length {len(instruction)}")
                instruction = enc.decode(instruction_encoded[:16385-15])   
            
            if request_counter >= 1:
                instruction = instruction[:-200 * request_counter]

            try:
                response = send_plain_request(instruction)
                rating = None
                if response == "Irrelevant (0)":
                    rating = 0
                if response == "Relevant (1)":
                    rating = 1
                if rating == None:
                    print("Error Response: ", response, instruction)
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
                        request_succeeded = True
                        break

            except Exception as ex:
                print(request_counter)
                if request_counter <= 5:
                    request_counter += 1
                    print("Error Request: ", idx, ex)
                
                elif request_counter > 5:
                    rt = RatedTable(
                            annotator="error",
                            query=hr_table.query,
                            query_id=hr_table.query_id,
                            relevancy=0,
                            table=hr_table.table,
                        )
                    rt.append_to_qrels(fp, 0)
                    rt.append_to_qrels(fp_err, 0)
                    request_succeeded = True
                    break

                else:
                    print("Error Request: ", idx, ex, instruction)
                    fp.close()
                    exit()

    fp.close()


if __name__ == '__main__':
    
    instructions = """
        You are an expert assessor making relevance judgments. You will be given a TREC topic and a table from a web page. 
        If this table provides no information about the topic (i.e., based on the context you would not expect this to be shown as a result from a search engine), answer “Irrelevant (0)”
        If this table provides relevant information about the topic (i.e., you would expect this Web page to be included in the search results from a search engine), answer “Relevant (1)”. 
        Topic: '$TOPIC'
        Table: ```
        $TABLE
        ```
        Relevant?
        """

    generate_qrels(instructions, "../gpt_judgements/rel_table_qrels.txt", "../gpt_judgements/rel_table_qrels_err.txt")
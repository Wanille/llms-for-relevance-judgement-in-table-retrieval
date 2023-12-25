import psycopg2
from tools import config, connect, read_tables, send_request, RatedTable, Table, remove_empty_rows, remove_empty_cols
import pandas as pd
import re
from random import shuffle, sample

params = config("database.ini")
conn, cur = connect(params)

def generate_qrels(system_instructions: str, instruction_pattern: str, topic_id: int, fn: str):
    human_rated_tables = read_tables(cur, topic_id)
    human_rated_tables_sub = sample(human_rated_tables, 20)

    fp = open(fn, "a")

    for hr_table in human_rated_tables_sub:
        remove_empty_cols(hr_table.table.relation)
        remove_empty_rows(hr_table.table.relation)
        instruction = re.sub(r"\$TOPIC", hr_table.query, instruction_pattern) 
        instruction = re.sub(r"\$TABLE", str(hr_table.table.relation), instruction)
        try:
            response = send_request(system_instructions, instruction)
            rating = None
            if response == "Irrelevant (0)":
                rating = 0
            if response == "Relevant (1)":
                rating = 1
            if response == "Highly relevant (2)":
                rating = 2
            
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
        You are an expert on web-tables and relevance judgements. Your instruction is to judge if the table is relevant to the provided topic. 
        Answer either and only with:
        Irrelevant (0): this table is irrelevant to the query (i.e., based on the context you would not expect this to be shown as a result from a search engine).
        Relevant (1): this table provides relevant information about the query (i.e., you would expect this Web page to be included in the search results from a search engine but not among the top results).
        Highly relevant (2): this table provides ideal information about the query (i.e., you would expect this Web page ranked near the top of the search results).
        """
    
    instruction_pattern = "Topic: '$TOPIC'\nTable: ```\n$TABLE\n```"
    
    generate_qrels(system_instructions, instruction_pattern, 1, "first_run.txt")
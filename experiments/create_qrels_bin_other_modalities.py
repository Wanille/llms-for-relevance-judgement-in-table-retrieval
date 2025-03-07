from LLmsfJiT import config, connect, get_tables_from_qrels, send_plain_request, RatedTable, get_rated_modalities_for_rated_table, load_client
import re
import json
from openai import OpenAI

params = config("../database.ini")
load_client(params["openai"]["apikey"])
conn, cur = connect(params["postgres"])

def generate_qrels(system_instructions: str, fn: str):
    human_rated_tables = get_tables_from_qrels(conn, cur, "../rel_files/rel_table_qrels_sample_100.txt")
    table_relevancies = get_rated_modalities_for_rated_table(cur, human_rated_tables)
    fp_entity = open(fn + "_entity.txt", "a")
    fp_text_before = open(fn + "_text_before.txt", "a")
    fp_text_after = open(fn + "_text_after.txt", "a")
    fp_page_title = open(fn + "_page_title.txt", "a")

    for hr_table, r_dict in zip(human_rated_tables, table_relevancies):
        instruction = re.sub(r"\$TOPIC", hr_table.query, system_instructions) 

        entity_str = json.dumps(hr_table.table.entities).encode('unicode-escape').decode()
        instruction_entity = re.sub(r"\$FIELD_TEXT", entity_str, instruction)
        instruction_entity = re.sub(r"\$FIELD_NAME", "Extracted entities from table", instruction_entity)

        text_before_str = hr_table.table.text_before
        instruction_text_before = re.sub(r"\$FIELD_TEXT", text_before_str, instruction)
        instruction_text_before = re.sub(r"\$FIELD_NAME", "Text before table", instruction_text_before)

        text_after_str = hr_table.table.text_after
        instruction_text_after = re.sub(r"\$FIELD_TEXT", text_after_str, instruction)
        instruction_text_after = re.sub(r"\$FIELD_NAME", "Text after table", instruction_text_after)

        page_title_str = hr_table.table.page_title
        instruction_page_title = re.sub(r"\$FIELD_TEXT", page_title_str, instruction)
        instruction_page_title = re.sub(r"\$FIELD_NAME", "Title of page containing table", instruction_page_title)

        response_entity = send_plain_request(instruction_entity)
        response_text_before = send_plain_request(instruction_text_before)
        response_text_after = send_plain_request(instruction_text_after)
        response_page_title = send_plain_request(instruction_page_title)

        RatedTable(hr_table.table, hr_table.query, parse_rating(response_page_title), "GPT", hr_table.query_id).append_to_qrels(fp_page_title)
        RatedTable(hr_table.table, hr_table.query, parse_rating(response_text_after), "GPT", hr_table.query_id).append_to_qrels(fp_text_after)
        RatedTable(hr_table.table, hr_table.query, parse_rating(response_text_before), "GPT", hr_table.query_id).append_to_qrels(fp_text_before)
        RatedTable(hr_table.table, hr_table.query, parse_rating(response_entity), "GPT", hr_table.query_id).append_to_qrels(fp_entity)
        

def parse_rating(response):
    rating = None
    if response == "Irrelevant (0)":
        rating = 0
    if response == "Relevant (1)":
        rating = 1

    if rating == None:
        print("Error Response: ", response)
    return rating


if __name__ == '__main__':
    
    system_instructions = """
        You are an expert assessor making relevance judgments on different table fields. You will be given a TREC topic and a table field (page title, text before the table, table, extracted entities, text after the table), from a web page. 
        If this table field provides no information about the topic (i.e., based on the context you would not expect this to be shown as a result from a search engine), answer “Irrelevant (0)”.
        If this table field provides relevant information about the topic (i.e., you would expect this Web page to be included in the search results from a search engine), answer “Relevant (1)”.
        Topic: '$TOPIC'
        $FIELD_NAME: 
        ```
        $FIELD_TEXT
        ```
        Relevant?
    """
    
    generate_qrels(system_instructions, "../gpt_judgements/ex_qrels_bin")
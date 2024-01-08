from io import TextIOWrapper
import json
from typing import Iterator
import psycopg2
from configparser import ConfigParser
from dataclasses import dataclass
from openai import OpenAI 

client = None

def load_client(OPENAI_API_KEY: str):
    global client
    client = OpenAI(api_key=OPENAI_API_KEY)


@dataclass
class Table:
    relation: list
    json_loc: str
    page_title: str = None
    title: str = None
    table_type: str = None
    has_header: bool = None
    text_before: str = None
    text_after: str = None
    entities: str = None
    

@dataclass
class RatedTable:
    table: Table
    query: str
    relevancy: int
    annotator: str
    query_id: int

    def to_json(self, it: int=0):
        return {
            "topic": self.query_id,
            "iteration": it,
            "json_loc": self.table.json_loc,
            "relevancy": float(self.relevancy)
        }

    def append_to_qrels(self, fp: TextIOWrapper, it: int=0) -> None:
        fp.write(f"{self.query_id}\t{it}\t{self.table.json_loc}\t{self.relevancy}\n")

def connect(params: dict):
    conn = psycopg2.connect(**params) 
    cur = conn.cursor()
    print("Connected to postgres")
    return conn, cur

def config(fn: str = "database.ini") -> dict:
    """Parses the database.ini config file
    Code used from https://www.postgresqltutorial.com/postgresql-python/connect/
    """
    parser = ConfigParser()
    parser.read(fn)
    sections = {}
    for section in parser.sections():
        section_params = {}
        params = parser.items(section=section)
        for param in params:
            section_params[param[0]] = param[1]
        sections[section] = section_params
    return sections

def read_trec_qrels(fn: str) -> dict:
    qrels_data = []
    with open(fn, 'r') as file:
        for line in file:
            line = line.strip().split()
            if len(line) == 4:
                qrels_data.append(line)
    return qrels_data

def read_trec_queries(fn: str) -> dict:
    queries = {}
    with open(fn, "r") as fp:
        for line in fp:
            line = line.strip().split(maxsplit=1)
            if len(line) == 2:
                query_id, query = line
                queries[query_id] = query  
            else:
                raise ValueError("queries file wrong format")             
    return queries 

def read_tables(cur, topic: int = -1) -> list[RatedTable]:
    q = f"""
        SELECT query, pt.page_title, wt.title, wt.relation, wt.table_type, tm.has_header, tb.text_before, ta.text_after, te.entities, relevancy, rel.json_loc, rel.topic FROM qrels rel
        JOIN queries q on rel.topic = q.qid
        JOIN web_table wt on rel.json_loc=wt.json_loc
        JOIN page_title pt on rel.json_loc=pt.json_loc
        JOIN table_meta tm on rel.json_loc=tm.json_loc
        JOIN text_before tb on rel.json_loc=tb.json_loc
        JOIN text_after ta on rel.json_loc=ta.json_loc
        JOIN table_entities te on rel.json_loc=te.json_loc
        """
    if topic != -1:
        q = q + f"\nWHERE topic = {topic}"

    cur.execute(q)
    results = cur.fetchall()
    tables = []
    for res in results:
        t = Table(
            res[3],
            res[10],
            res[1],
            res[2],
            res[4],
            res[5],
            res[6],
            res[7],
            res[8],
            )
        rt = RatedTable(
            t,
            res[0],
            res[9],
            "HUMAN",
            res[11],
        )
        tables.append(rt)
    return tables

def get_tables_from_qrels(conn, cur, qrels_fn: str) -> list[RatedTable]:
    qrels = read_trec_qrels(qrels_fn)
    json_locs = list(zip(*qrels))[2]
    topics = list(zip(*qrels))[0]

    cur.execute("CREATE TEMPORARY TABLE temp_qrels (json_loc text)")
    for json_loc in json_locs:
        cur.execute(cur.mogrify("INSERT INTO temp_qrels (json_loc) VALUES (%s)", (json_loc,)))
    conn.commit()

    q = f"""
        SELECT wt.json_loc, pt.page_title, wt.title, wt.relation, wt.table_type, tm.has_header, tb.text_before, ta.text_after, te.entities FROM web_table wt 
        JOIN page_title pt on wt.json_loc=pt.json_loc
        JOIN table_meta tm on wt.json_loc=tm.json_loc
        JOIN text_before tb on wt.json_loc=tb.json_loc
        JOIN text_after ta on wt.json_loc=ta.json_loc
        JOIN table_entities te on wt.json_loc=te.json_loc
        RIGHT JOIN temp_qrels tq on wt.json_loc=tq.json_loc
        """
    
    cur.execute(q)
    results = cur.fetchall()
    tables = {}
    for res in results:
        tables[res[0]] = Table(
                json_loc=res[0],
                entities=res[8],
                has_header=res[5],
                page_title=res[1],
                relation=res[3],
                table_type=res[4],
                text_after=res[7],
                text_before=res[6],
                title=res[2]
                ) 
    
    q2 = f"""
        SELECT * FROM queries q
        """
    cur.execute(q2)
    queries = {}
    for q in cur.fetchall():
        queries[q[0]] = q[1]
    human_rated_tables = []
    for j in qrels:
        human_rated_tables.append(
            RatedTable(
                table=tables[j[2]],
                annotator="HUMAN",
                query=queries[int(j[0])],
                query_id=j[0],
                relevancy=j[3]
            )
        )
    
    cur.execute("DROP TABLE temp_qrels")

    return human_rated_tables 

def get_rated_modalities_for_rated_table(cur, tables: list[RatedTable]): 
    relevancies = [] 
    for t in tables:
        r_dict = {}
        cur.execute("SELECT relevancy from qrels_page_title t where t.topic = %s AND t.json_loc = %s", (t.query_id, t.table.json_loc))
        r_dict["page_title"] = cur.fetchone()[0]
        cur.execute("SELECT relevancy from qrels_text_before t where t.topic = %s AND t.json_loc = %s", (t.query_id, t.table.json_loc))
        r_dict["text_before"] = cur.fetchone()[0]
        cur.execute("SELECT relevancy from qrels_text_after t where t.topic = %s AND t.json_loc = %s", (t.query_id, t.table.json_loc))
        r_dict["text_after"] = cur.fetchone()[0]
        cur.execute("SELECT relevancy from qrels_entities t where t.topic = %s AND t.json_loc = %s", (t.query_id, t.table.json_loc))
        r_dict["entities"] = cur.fetchone()[0]
        r_dict["table"] = t.relevancy
        relevancies.append(r_dict)
    return relevancies
   


def send_request(system_instructions: str, instructions: str) -> str:
    if client is None:
        raise ConnectionError("Load OpenAi client first using `load_client(OPENAI_API_KEY)`") 
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-16k",
    messages=[
      {"role": "system", "content": system_instructions},
      {"role": "user", "content": instructions}
      ],
      temperature=0
    )
    return response.choices[0].message.content 

def send_plain_request(instructions: str) -> str:
    if client is None:
        raise ConnectionError("Load OpenAi client first using `load_client(OPENAI_API_KEY)`") 
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-16k",
    messages=[
      {"role": "user", "content": instructions}
      ],
      temperature=0
    )
    return response.choices[0].message.content 

def send_request_messages(messages: list[dict[str]]) -> str:
    if client is None:
        raise ConnectionError("Load OpenAi client first using `load_client(OPENAI_API_KEY)`") 
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-16k",
    messages=messages,
      temperature=0
    )
    return response.choices[0].message.content 

def remove_empty_rows(table: list):
    rows_to_drop = []
    for idx, row in enumerate(table):
        if not any(entry != '' for entry in row):
            rows_to_drop.append((idx))
    
    rows_to_drop.reverse()

    for idx in rows_to_drop:
        del table[idx]

def remove_empty_cols(table: list):
    cols_to_drop = set(range(len(table[0])))
    for row in table:
        for idx, col in enumerate(row):
            if col != '' and idx in cols_to_drop:
                cols_to_drop.remove(idx)
    
    cols_to_drop = list(cols_to_drop)
    cols_to_drop.reverse()
    for row in table:
        for idx in cols_to_drop:
            del row[idx]


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

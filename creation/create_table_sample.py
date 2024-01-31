import psycopg2
from LLmsfJiT import config, connect
from random import sample

conf = config("../database.ini")
conn, cur = connect(conf["postgres"])




cur.execute("SELECT json_loc FROM web_table")
all_tables = cur.fetchmany()

tables_sampled = sample(all_tables, )
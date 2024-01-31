from LLmsfJiT import read_trec_qrels, connect, config
from random import sample

params = config("../database.ini")
conn, cur = connect(params["postgres"])

def main():
    cur.execute("SELECT * FROM qrels")
    qrels = cur.fetchall()
    # qrels = read_trec_qrels("rel_files/rel_table_qrels.txt")
    
    grels_sample = sample(qrels, 1000)

    with open("../rel_files/rel_table_qrels_sample_1000.txt", "w") as fp:
        for q in grels_sample:
            fp.write(f"{q[0]}\t{q[1]}\t{q[2]}\t{q[3]}\n")


if __name__ == '__main__':
    main()


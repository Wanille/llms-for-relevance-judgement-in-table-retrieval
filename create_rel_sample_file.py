from tools import read_trec_qrels, connect, config
from random import sample

params = config("database.ini")
conn, cur = connect(params)

def main():
    cur.execute("SELECT * FROM qrels")
    qrels = cur.fetchall()
    # qrels = read_trec_qrels("rel_files/rel_table_qrels.txt")
    qgrades = {
        0: [],
        1: [],
        2: []
    }
    for q in qrels:
       qgrades[q[-1]].append(q) 

    qgrades_sample = []
    for key in qgrades.keys():      
        qgrades_sample.extend(sample(qgrades[key], 30))

    with open("rel_files/rel_table_qrels_sample_balanced.txt", "w") as fp:
        for q in qgrades_sample:
            fp.write(f"{q[0]}\t{q[1]}\t{q[2]}\t{q[3]}\n")


if __name__ == '__main__':
    main()


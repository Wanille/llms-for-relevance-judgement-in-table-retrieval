# LLMs for relevance judgement in table retrieval



## Steps to reproduce experiments 


### Download files 📂

Download the following files and place them inside the `rel_files/` directory.
- `https://github.com/Zhiyu-Chen/Web-Table-Retrieval-Benchmark/blob/main/data/rel_PageTitle_qrels.txt`
- `https://github.com/Zhiyu-Chen/Web-Table-Retrieval-Benchmark/blob/main/data/rel_entity_qrels.txt`
- `https://github.com/Zhiyu-Chen/Web-Table-Retrieval-Benchmark/blob/main/data/rel_table_qrels.txt `
- `https://github.com/Zhiyu-Chen/Web-Table-Retrieval-Benchmark/blob/main/data/rel_textAfter_qrels.txt`
- `https://github.com/Zhiyu-Chen/Web-Table-Retrieval-Benchmark/blob/main/data/rel_textBefore_qrels.txt`

Download the WTR dump into the root of this Git repository.  
- `http://www.cse.lehigh.edu/~brian/data/WTR_tables.tar.gz`   

Unzip the dump with `gunzip WTR_tables.tar.gz`.  
Untar the decompressed directory using `tar -xf WTR_tables.gz`.  

### Setup dependencies 🔧
Install the newest JDK version (e.g. `sudo apt install -y default-jdk`).  
Setup a postgres instance and create a database called `web_tables`.  
Install the required python packages from `requirements.txt` 

### Setup the config file 📋
Into the root of this Git repository add a file called `database.ini`.  
The file should look like this:

```
[postgres]
host=HOST_IP_ADDRESS
database=web_tables
user=POSTGRES_USER
password=POSTGRES_PASSWORD

[openai]
apikey=OPENAI_API_KEY
```

### Insert the data 📃
Run `cd creation` and `python insert_data.py` to insert your data into the postgres db. 


### Run the experiments 🔬

Now run the experiments by moving into the experiment dir and executing the python scripts :).

### Evaluation 📊

All evaluation notebooks can be found under `notebooks/`.

### Dataset analysis 📈

An additional Notebook analysing table metadata can be found under `dataset_analysis`.
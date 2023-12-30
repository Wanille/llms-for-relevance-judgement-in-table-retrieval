DROP TABLE IF EXISTS "web_table";
DROP TABLE IF EXISTS "table_meta";
DROP TABLE IF EXISTS "text_before";
DROP TABLE IF EXISTS "text_after";
DROP TABLE IF EXISTS "table_entities";
DROP TABLE IF EXISTS "page_title";
DROP TABLE IF EXISTS "queries";
DROP TABLE IF EXISTS "qrels";
DROP TABLE IF EXISTS "trec_qrels";

-- -------------------------------------
-- Table "table"
-- -------------------------------------
CREATE TABLE if not exists "web_table"
(
    "json_loc" text not null UNIQUE,
    "title" text,
    "relation" JSON,
    "table_type" text,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "table_meta"
-- -------------------------------------
CREATE TABLE if not exists "table_meta" 
(
    "json_loc" text not null UNIQUE,
    "has_key_column" Boolean,
    "key_column_index" int,
    "has_header" Boolean,
    "header_pos" text,
    "header_row_index" int,
    "table_orientation" text,
    "table_num" int,
    "record_end_offset" int,
    "record_offset" int,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "text_before"
-- -------------------------------------
CREATE TABLE if not exists "text_before" 
(
    "json_loc" text not null UNIQUE,
    "text_before" text,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "text_after"
-- -------------------------------------
CREATE TABLE if not exists "text_after" 
(
    "json_loc" text not null UNIQUE,
    "text_after" text,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "table_entities"
-- -------------------------------------
CREATE TABLE if not exists "table_entities" 
(
    "json_loc" text not null UNIQUE,
    "entities" JSON,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "page_title"
-- -------------------------------------
CREATE TABLE if not exists "page_title" 
(
    "json_loc" text not null UNIQUE,
    "page_title" text,
    primary key ("json_loc")
);

-- -------------------------------------
-- Table "queries"
-- -------------------------------------
CREATE TABLE if not exists "queries"
(
    "qid" int not null UNIQUE,
    "query" text
);

-- -------------------------------------
-- Table "qrels"
-- -------------------------------------
CREATE TABLE if not exists "qrels"
(
    "topic" int not null,
    "iteration" int,
    "json_loc" text not null,
    "relevancy" int not null
);

-- -------------------------------------
-- Table "qrels_entities"
-- -------------------------------------
CREATE TABLE if not exists "qrels_entities"
(
    "topic" int not null,
    "iteration" int,
    "json_loc" text not null,
    "relevancy" int not null
);

-- -------------------------------------
-- Table "qrels_page_title"
-- -------------------------------------
CREATE TABLE if not exists "qrels_page_title"
(
    "topic" int not null,
    "iteration" int,
    "json_loc" text not null,
    "relevancy" int not null
);

-- -------------------------------------
-- Table "qrels_text_after"
-- -------------------------------------
CREATE TABLE if not exists "qrels_text_after"
(
    "topic" int not null,
    "iteration" int,
    "json_loc" text not null,
    "relevancy" int not null
);

-- -------------------------------------
-- Table "qrels_text_before"
-- -------------------------------------
CREATE TABLE if not exists "qrels_text_before"
(
    "topic" int not null,
    "iteration" int,
    "json_loc" text not null,
    "relevancy" int not null
);
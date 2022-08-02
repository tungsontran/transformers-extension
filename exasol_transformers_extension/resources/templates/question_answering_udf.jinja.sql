CREATE OR REPLACE {{ language_alias }} SET SCRIPT "TE_QUESTION_ANSWERING_UDF"(
    device_id INTEGER,
    bucketfs_conn VARCHAR(2000000),
    sub_dir VARCHAR(2000000),
    model_name VARCHAR(2000000),
    question VARCHAR(2000000),
    context_text VARCHAR(2000000)
    ORDER BY model_name
)EMITS (
    bucketfs_conn VARCHAR(2000000),
    sub_dir VARCHAR(2000000),
    model_name VARCHAR(2000000),
    question VARCHAR(2000000),
    context_text VARCHAR(2000000),
    answer VARCHAR(2000000),
    score DOUBLE ) AS

{{ script_content }}

/
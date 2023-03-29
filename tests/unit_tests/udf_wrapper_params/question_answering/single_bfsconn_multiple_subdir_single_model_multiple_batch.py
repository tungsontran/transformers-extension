from pathlib import PurePosixPath
from exasol_udf_mock_python.connection import Connection
from tests.unit_tests.udf_wrapper_params.question_answering.\
    mock_question_answering import \
    MockQuestionAnsweringFactory, MockQuestionAnsweringModel, MockPipeline


def udf_wrapper():
    from exasol_udf_mock_python.udf_context import UDFContext
    from exasol_transformers_extension.udfs.models.question_answering_udf import \
        QuestionAnsweringUDF
    from tests.unit_tests.udf_wrapper_params.question_answering. \
        mock_sequence_tokenizer import MockSequenceTokenizer
    from tests.unit_tests.udf_wrapper_params.question_answering.\
        single_bfsconn_multiple_subdir_single_model_multiple_batch import \
        SingleBucketFSConnMultipleSubdirSingleModelNameMultipleBatch as params

    udf = QuestionAnsweringUDF(
        exa,
        batch_size=params.batch_size,
        pipeline=params.mock_pipeline,
        base_model=params.mock_factory,
        tokenizer=MockSequenceTokenizer)

    def run(ctx: UDFContext):
        udf.run(ctx)


class SingleBucketFSConnMultipleSubdirSingleModelNameMultipleBatch:
    """
    single bucketfs connection, multiple subdir, single model, multiple batch
    """
    batch_size = 2
    data_size = 2
    top_k = 2

    input_data = [(None, "bfs_conn1", "sub_dir1", "model1",
                   "question", "context", top_k)] * data_size + \
                 [(None, "bfs_conn1", "sub_dir2", "model1",
                   "question", "context", top_k)] * data_size
    output_data = [("bfs_conn1", "sub_dir1", "model1", "question", "context",
                    top_k, "answer 1", 0.1, 1, None)] * data_size * top_k + \
                  [("bfs_conn1", "sub_dir2", "model1", "question", "context",
                    top_k, "answer 2", 0.2, 1, None)] * data_size * top_k

    tmpdir_name = "_".join(("/tmpdir", __qualname__))
    base_cache_dir1 = PurePosixPath(tmpdir_name, "bfs_conn1")
    bfs_connections = {
        "bfs_conn1": Connection(address=f"file://{base_cache_dir1}")}

    mock_factory = MockQuestionAnsweringFactory({
        PurePosixPath(base_cache_dir1, "sub_dir1", "model1"):
            MockQuestionAnsweringModel(answer="answer 1", score=0.1, rank=1),
        PurePosixPath(base_cache_dir1, "sub_dir2", "model1"):
            MockQuestionAnsweringModel(answer="answer 2", score=0.2, rank=1),
    })

    mock_pipeline = MockPipeline
    udf_wrapper = udf_wrapper


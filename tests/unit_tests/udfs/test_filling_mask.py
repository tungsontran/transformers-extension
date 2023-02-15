import pytest
from exasol_udf_mock_python.column import Column
from exasol_udf_mock_python.group import Group
from exasol_udf_mock_python.mock_exa_environment import MockExaEnvironment
from exasol_udf_mock_python.mock_meta_data import MockMetaData
from exasol_udf_mock_python.udf_mock_executor import UDFMockExecutor
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_bfsconn_single_subdir_single_model_multiple_batch import \
    MultipleBucketFSConnSingleSubdirSingleModelNameMultipleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_bfsconn_single_subdir_single_model_single_batch import \
    MultipleBucketFSConnSingleSubdirSingleModelNameSingleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_model_multiple_batch_complete import \
    MultipleModelMultipleBatchComplete
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_model_multiple_batch_incomplete import \
    MultipleModelMultipleBatchIncomplete
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_model_multiple_batch_multiple_models_per_batch import \
    MultipleModelMultipleBatchMultipleModelsPerBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_model_single_batch_complete import \
    MultipleModelSingleBatchComplete
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_model_single_batch_incomplete import \
    MultipleModelSingleBatchIncomplete
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_topk_single_model_multiple_batch import \
    MultipleTopkSingleModelNameMultipleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.multiple_topk_single_model_single_batch import \
    MultipleTopkSingleModelNameSingleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.single_bfsconn_multiple_subdir_single_model_multiple_batch import \
    SingleBucketFSConnMultipleSubdirSingleModelNameMultipleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.single_bfsconn_multiple_subdir_single_model_single_batch import \
    SingleBucketFSConnMultipleSubdirSingleModelNameSingleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.single_model_multiple_batch_complete import \
    SingleModelMultipleBatchComplete
from tests.unit_tests.udf_wrapper_params.filling_mask.single_model_multiple_batch_incomplete import \
    SingleModelMultipleBatchIncomplete
from tests.unit_tests.udf_wrapper_params.filling_mask.single_model_single_batch_complete import \
    SingleModelSingleBatchComplete
from tests.unit_tests.udf_wrapper_params.filling_mask.single_model_single_batch_incomplete import \
    SingleModelSingleBatchIncomplete
from tests.unit_tests.udf_wrapper_params.filling_mask.single_topk_multiple_model_multiple_batch import \
    SingleTopkMultipleModelNameMultipleBatch
from tests.unit_tests.udf_wrapper_params.filling_mask.single_topk_multiple_model_single_batch import \
    SingleTopkMultipleModelNameSingleBatch


def create_mock_metadata(udf_wrapper):
    meta = MockMetaData(
        script_code_wrapper_function=udf_wrapper,
        input_type="SET",
        input_columns=[
            Column("device_id", int, "INTEGER"),
            Column("bucketfs_conn", str, "VARCHAR(2000000)"),
            Column("sub_dir", str, "VARCHAR(2000000)"),
            Column("model_name", str, "VARCHAR(2000000)"),
            Column("text_data", str, "VARCHAR(2000000)"),
            Column("top_k", int, "INTEGER")
        ],
        output_type="EMITS",
        output_columns=[
            Column("bucketfs_conn", str, "VARCHAR(2000000)"),
            Column("sub_dir", str, "VARCHAR(2000000)"),
            Column("model_name", str, "VARCHAR(2000000)"),
            Column("text_data", str, "VARCHAR(2000000)"),
            Column("top_k", int, "INTEGER"),
            Column("filled_text", str, "VARCHAR(2000000)"),
            Column("score", float, "DOUBLE"),
            Column("rank", int, "INTEGER")
        ],
    )
    return meta


@pytest.mark.parametrize("params", [
    SingleModelSingleBatchComplete,
    SingleModelSingleBatchIncomplete,
    SingleModelMultipleBatchComplete,
    SingleModelMultipleBatchIncomplete,
    MultipleModelSingleBatchComplete,
    MultipleModelSingleBatchIncomplete,
    MultipleModelMultipleBatchComplete,
    MultipleModelMultipleBatchIncomplete,
    MultipleModelMultipleBatchMultipleModelsPerBatch,
    MultipleBucketFSConnSingleSubdirSingleModelNameSingleBatch,
    MultipleBucketFSConnSingleSubdirSingleModelNameMultipleBatch,
    SingleBucketFSConnMultipleSubdirSingleModelNameSingleBatch,
    SingleBucketFSConnMultipleSubdirSingleModelNameMultipleBatch,
    MultipleTopkSingleModelNameMultipleBatch,
    MultipleTopkSingleModelNameSingleBatch,
    SingleTopkMultipleModelNameSingleBatch,
    SingleTopkMultipleModelNameMultipleBatch
])
def test_filling_mask(params):
    executor = UDFMockExecutor()
    meta = create_mock_metadata(params.udf_wrapper)

    exa = MockExaEnvironment(
        metadata=meta,
        connections=params.bfs_connections)

    result = executor.run([Group(params.input_data)], exa)
    assert result[0].rows == params.output_data

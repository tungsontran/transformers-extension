import torch
import pytest
import pandas as pd
from typing import Dict
from tests.utils.parameters import model_params
from exasol_udf_mock_python.connection import Connection
from exasol_transformers_extension.udfs.models.filling_mask_udf import \
    FillingMaskUDF


class ExaEnvironment:
    def __init__(self, connections: Dict[str, Connection] = None):
        self._connections = connections
        if self._connections is None:
            self._connections = {}

    def get_connection(self, name: str) -> Connection:
        return self._connections[name]


class Context:
    def __init__(self, input_df):
        self.input_df = input_df
        self._emitted = []
        self._is_accessed_once = False

    def emit(self, *args):
        self._emitted.append(args)

    def reset(self):
        self._is_accessed_once = False

    def get_emitted(self):
        return self._emitted

    def get_dataframe(self, num_rows='all', start_col=0):
        return_df = None if self._is_accessed_once \
            else self.input_df[self.input_df.columns[start_col:]]
        self._is_accessed_once = True
        return return_df


@pytest.mark.parametrize(
    "description,  device_id, n_rows", [
        ("on CPU with batch input", None, 3),
        ("on CPU with single input", None, 1),
        ("on GPU with batch input", 0, 3),
        ("on GPU with single input", 0, 1)
    ])
def test_filling_mask_udf(
        description, device_id, n_rows, upload_base_model_to_local_bucketfs):

    if device_id is not None and not torch.cuda.is_available():
        pytest.skip(f"There is no available device({device_id}) "
                    f"to execute the test")

    bucketfs_base_path = upload_base_model_to_local_bucketfs
    bucketfs_conn_name = "bucketfs_connection"
    bucketfs_connection = Connection(address=f"file://{bucketfs_base_path}")

    top_k = 3
    batch_size = 2
    text_data = "Exasol is an analytics <mask> management software company."
    sample_data = [(
        None,
        bucketfs_conn_name,
        model_params.sub_dir,
        model_params.base_model,
        text_data,
        top_k
    ) for _ in range(n_rows)]
    columns = [
        'device_id',
        'bucketfs_conn',
        'sub_dir',
        'model_name',
        'text_data',
        'top_k']

    sample_df = pd.DataFrame(data=sample_data, columns=columns)
    ctx = Context(input_df=sample_df)
    exa = ExaEnvironment({bucketfs_conn_name: bucketfs_connection})

    sequence_classifier = FillingMaskUDF(exa, batch_size=batch_size)
    sequence_classifier.run(ctx)

    result_df = ctx.get_emitted()[0][0]
    new_columns = ['filled_text', 'score', 'rank']

    # assertions
    is_score_typed_as_float = result_df['score'].dtypes == 'float'
    is_rank_typed_as_int = result_df['rank'].dtypes == 'int'
    has_valid_shape =  \
        result_df.shape == (n_rows * top_k, len(columns)+len(new_columns)-1)
    has_valid_column_number = \
        result_df.shape[1] == len(columns) + len(new_columns) - 1
    is_rank_correct = \
        all([result_df[row*top_k: top_k + row*top_k]
            .sort_values(by='score', ascending=False)['rank']
            .is_monotonic for row in range(n_rows)])

    assert all((
        is_score_typed_as_float,
        is_rank_typed_as_int,
        has_valid_shape,
        has_valid_column_number,
        is_rank_correct
    ))


from tests.unit_tests.udf_wrapper_params.sequence_classification.\
    MockSequenceClassificationFactory import \
    Config, MockSequenceClassificationFactory, MockSequenceClassificationModel


def udf_wrapper():
    from exasol_udf_mock_python.udf_context import UDFContext
    from exasol_transformers_extension.udfs. \
        sequence_classification_single_text_udf import \
        SequenceClassificationSingleText
    from tests.unit_tests.udf_wrapper_params.sequence_classification. \
        MockSequenceTokenizer import MockSequenceTokenizer
    from tests.unit_tests.udf_wrapper_params.sequence_classification.\
        SingleModelMultipleBatchComplete import \
        SingleModelMultipleBatchComplete as params

    udf = SequenceClassificationSingleText(
        exa,
        cache_dir="dummy_cache_dir",
        batch_size=params.batch_size,
        base_model=params.mock_factory,
        tokenizer=MockSequenceTokenizer)

    def run(ctx: UDFContext):
        udf.run(ctx)


class SingleModelMultipleBatchComplete:
    """
    single model, multiple batch, last batch complete
    """

    batch_size = 2
    data_size = 4

    config = Config({
        0: 'label1', 1: 'label2',
        2: 'label3', 3: 'label4'})

    logits = [0.1, 0.2, 0.3, 0.4]

    mock_factory = MockSequenceClassificationFactory({
        "model1": MockSequenceClassificationModel(
            config=config,
            logits=logits)
    })

    inputs = [("sub_dir1", "model1", "My test text")] * data_size

    outputs = [("sub_dir1", "model1", "My test text", "label1", 0.21),
               ("sub_dir1", "model1", "My test text", "label2", 0.24),
               ("sub_dir1", "model1", "My test text", "label3", 0.26),
               ("sub_dir1", "model1", "My test text", "label4", 0.29)] * 4

    udf_wrapper = udf_wrapper

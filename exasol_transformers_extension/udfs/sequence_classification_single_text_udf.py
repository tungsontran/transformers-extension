import torch
import transformers
from exasol_transformers_extension.udfs import bucketfs_operations


class SequenceClassificationSingleText:
    def __init__(self,
                 exa,
                 cache_dir=None,
                 base_model=transformers.AutoModelForSequenceClassification,
                 tokenizer=transformers.AutoTokenizer):
        self.exa = exa
        self.cache_dir = cache_dir
        self.base_model = base_model
        self.tokenizer = tokenizer

    def run(self, ctx):
        bucketfs_conn = ctx.bucketfs_conn
        text = ctx.text
        model_name = ctx.model_name

        # get bucketfs location
        bucketfs_conn_obj = self.exa.get_connection(bucketfs_conn)
        bucketfs_location = bucketfs_operations.create_bucketfs_location(
            bucketfs_conn_obj)

        # get cache directory
        if not self.cache_dir:
            model_path = bucketfs_operations.get_model_path(model_name)
            self.cache_dir = bucketfs_operations.get_local_bucketfs_path(
                bucketfs_location=bucketfs_location,
                model_path=model_path)

        # load models
        model = self.base_model.from_pretrained(
            model_name, cache_dir=self.cache_dir)
        tokenizer = self.tokenizer.from_pretrained(
            model_name, cache_dir=self.cache_dir)

        # perform prediction
        tokens = tokenizer(text, return_tensors="pt")
        logits = model(**tokens).logits
        predictions = torch.softmax(logits, dim=1).tolist()[0]
        ctx.emit(*predictions)

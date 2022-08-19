import torch
import pandas as pd
import transformers
from typing import Tuple, List

from exasol_transformers_extension.deployment import constants
from exasol_transformers_extension.utils import device_management, \
    dataframe_operations, bucketfs_operations


class QuestionAnswering:
    def __init__(self,
                 exa,
                 batch_size=100,
                 pipeline=transformers.pipeline,
                 base_model=transformers.AutoModelForQuestionAnswering,
                 tokenizer=transformers.AutoTokenizer):
        self.exa = exa
        self.bacth_size = batch_size
        self.pipeline = pipeline
        self.base_model = base_model
        self.tokenizer = tokenizer
        self.device = None
        self.cache_dir = None
        self.last_loaded_model_key = None
        self.last_loaded_model = None
        self.last_loaded_tokenizer = None
        self.last_created_pipeline = None

    def run(self, ctx):
        device_id = ctx.get_dataframe(1).iloc[0]['device_id']
        self.device = device_management.get_torch_device(device_id)
        ctx.reset()

        while True:
            batch_df = ctx.get_dataframe(num_rows=self.bacth_size, start_col=1)
            if batch_df is None:
                break

            result_df = self.get_batched_predictions(batch_df)
            ctx.emit(result_df)

        self.clear_device_memory()

    def get_batched_predictions(self, batch_df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform separate predictions for each model in the dataframe. If the
        model is not cached, it is loaded into the cache before the prediction.

        :param batch_df: A batch of dataframe retrieved from context

        :return: Prediction results of the corresponding dataframe
        """
        result_df_list = []
        unique_values = dataframe_operations.get_unique_values(
            batch_df, constants.ORDERED_COLUMNS, sort=True)
        for model_name, bucketfs_conn, sub_dir in unique_values:
            model_df = batch_df[
                (batch_df['model_name'] == model_name) &
                (batch_df['bucketfs_conn'] == bucketfs_conn) &
                (batch_df['sub_dir'] == sub_dir)]

            current_model_key = (bucketfs_conn, sub_dir, model_name)
            if self.last_loaded_model_key != current_model_key:
                self.set_cache_dir(model_df)
                self.clear_device_memory()
                self.load_models(model_name)
                self.last_loaded_model_key = current_model_key

            unique_params = dataframe_operations.get_unique_values(
                model_df, ['top_k'])
            for top_k in unique_params:
                param_based_model_df = model_df[model_df['top_k'] == top_k[0]]
                pred_df = self.get_prediction(param_based_model_df)
                result_df_list.append(pred_df)

        result_df = pd.concat(result_df_list)
        return result_df

    def set_cache_dir(self, model_df: pd.DataFrame) -> None:
        """
        Set the cache directory in bucketfs of the specified model. Note that,
        cache_dir class variable is used for testing purpose. This variable is
        set to a local path only in unit tests.

        :param model_df: The model dataframe to set the cache directory
        """
        model_name = model_df['model_name'].iloc[0]
        bucketfs_conn_name = model_df['bucketfs_conn'].iloc[0]
        sub_dir = model_df['sub_dir'].iloc[0]
        bucketfs_location = bucketfs_operations.create_bucketfs_location(
            self.exa.get_connection(bucketfs_conn_name))

        model_path = bucketfs_operations.get_model_path(sub_dir, model_name)
        self.cache_dir = bucketfs_operations.get_local_bucketfs_path(
            bucketfs_location=bucketfs_location, model_path=str(model_path))

    def load_models(self, model_name: str) -> None:
        """
        Load model and tokenizer model from the cached location in bucketfs

        :param model_name: The model name to be loaded
        """
        self.last_loaded_model = self.base_model.from_pretrained(
            model_name, cache_dir=self.cache_dir)
        self.last_loaded_tokenizer = self.tokenizer.from_pretrained(
            model_name, cache_dir=self.cache_dir)
        self.last_created_pipeline = self.pipeline(
            "question-answering",
            model=self.last_loaded_model,
            tokenizer=self.last_loaded_tokenizer,
            device=self.device,
            framework="pt")

    def get_prediction(self, model_df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform prediction of the given model and preparation of the prediction
        results according to the format that the UDF can emit.

        :param model_df: The dataframe to be predicted

        :return: The dataframe where the model_df is formatted with the
        prediction results
        """
        pred_df_list = self._predict_model(model_df)
        pred_df = self._prepare_prediction_dataframe(model_df, pred_df_list)
        return pred_df

    def _predict_model(self, model_df: pd.DataFrame) -> List[pd.DataFrame]:
        """
        Predict the given text list using recently loaded models, return
        probability scores and labels

        :param model_df: The dataframe to be predicted

        :return: List of dataframes holding prediction results
        """
        questions = list(model_df['question'])
        contexts = list(model_df['context_text'])
        top_k = int(model_df['top_k'].iloc[0])
        results = self.last_created_pipeline(
            question=questions, context=contexts, top_k=top_k)

        # We need to separate the answer to one question from the answers to
        # multiple questions, such that results of one question could be
        # - a dict where top_k=1, or
        # - either a dict or list of dicts where top_k>1
        # in both cases we need to put the answer(s) in a list to make sure that
        # the answer(s) is from a single question
        results = [results] if len(questions) == 1 else results

        columns = ["answer", "score"]
        results_df_list = []
        for result in results:
            result_df = pd.DataFrame([result]) if type(result) == dict \
                else pd.DataFrame(result)
            results_df_list.append(result_df[columns])

        return results_df_list

    @staticmethod
    def _prepare_prediction_dataframe(
            model_df: pd.DataFrame, pred_df_list: List[pd.DataFrame]) \
            -> pd.DataFrame:
        """
        Reformat the dataframe used in prediction, such that each input rows
        has a row for each label and its probability score

        :param model_df: Dataframe used in prediction
        :param pred_df_list: List of dataframes holding prediction results

        :return: Prepared dataframe including input data and predictions
        """
        n_topk_results = list(map(lambda x: x.shape[0], pred_df_list))
        repeated_indexes = model_df.index.repeat(repeats=n_topk_results)
        model_df = model_df.loc[repeated_indexes].reset_index(drop=True)

        # Concat predictions and model_df
        pred_df = pd.concat(pred_df_list, axis=0).reset_index(drop=True)
        model_df = pd.concat([model_df, pred_df], axis=1)

        return model_df

    def clear_device_memory(self):
        """
        Delete models and free device memory
        """

        del self.last_loaded_model
        del self.last_loaded_tokenizer
        torch.cuda.empty_cache()
from typing import Union

from qoa4ml.utils.logger import qoa_logger


# ---------------------------------------------------------
def average_probability(predictions: list, request_id: str) -> Union[dict, None]:
    """
    Aggregates the probabilities of predictions from multiple models for ensemble classification.

    Args:
        data (List[dict]): List of dictionaries containing model predictions.
                           Each dictionary must have a "prediction" field which is a list of [class, probability].
        request_id (str): Unique identifier for the request.

    Returns:
        Union[Dict, None]: Aggregated results including mean probabilities, or None if not enough data.
    """
    if len(predictions) < 2:
        qoa_logger.error("No aggregation needed for only one prediction")
        return None

    class_probabilities = {}

    for class_id, probability in predictions:
        if class_id not in class_probabilities:
            class_probabilities[class_id] = []
        class_probabilities[class_id].append(probability)
    # for prediction_dict in predictions:
    #     prediction_list = prediction_dict.get("prediction")
    #     if not prediction_list or len(prediction_list) != 2:
    #         print(
    #             "Invalid prediction format: each prediction must be a list of [class, probability]"
    #         )
    #         return None
    #
    #     class_id, probability = prediction_list
    #     if class_id not in class_probabilities:
    #         class_probabilities[class_id] = []
    #     class_probabilities[class_id].append(probability)
    aggregated_predictions = []

    for class_id, probabilities in class_probabilities.items():
        total = sum(probabilities)
        count = len(probabilities)
        mean_probability = total / count
        aggregated_predictions.append([class_id, mean_probability])

    aggregated_result = {
        "request_id": request_id,
        "prediction": aggregated_predictions,
    }

    return aggregated_result


# def weighted_average_probability(data: list, weights: list) -> Union[dict, None]:
#     if len(data) < 2:
#         qoa_logger.error("No aggregation needed for only one prediction")
#         return None
#     if len(data) != len(weights):
#         qoa_logger.error(
#             f"Data and weights need to have the same size:\ndata:{len(data)}\nweights:{len(weights)}"
#         )
#         return None
#
#     req_id = data[0]["request_id"]
#
#     aggregated_predictions = []
#     pipeline_ids = []
#     inference_model_ids = []
#
#     for entry, weight in zip(data, weights, strict=True):
#         weighted_prediction = np.array(entry["prediction"]) * weight
#         aggregated_predictions.append(weighted_prediction)
#         pipeline_ids.append(entry["pipeline_id"])
#         inference_model_ids.append(entry["inference_model_id"])
#
#     mean_prediction = np.sum(aggregated_predictions, axis=0)
#
#     aggregated_result = {
#         "request_id": req_id,
#         "prediction": mean_prediction.tolist(),
#         "pipeline_id": ",".join(pipeline_ids),
#         "inference_model_id": ",".join(inference_model_ids),
#     }
#
#     return aggregated_result
#
#
# def rank_averaging(data: list) -> Union[dict, None]:
#     if len(data) < 2:
#         qoa_logger.error("No aggregation needed for only one prediction")
#         return None
#
#     req_id = data[0]["request_id"]
#     aggregated_predictions = []
#     pipeline_ids = []
#     inference_model_ids = []
#
#     for entry in data:
#         aggregated_predictions.append(entry["prediction"])
#         pipeline_ids.append(entry["pipeline_id"])
#         inference_model_ids.append(entry["inference_model_id"])
#
#     # Rank the predictions
#     ranks = []
#     for predictions in aggregated_predictions:
#         ranks.append(np.argsort(np.argsort(predictions)))
#
#     # Average the ranks
#     average_ranks = np.mean(ranks, axis=0)
#
#     # Convert ranks back into prediction values
#     min_val = np.min(aggregated_predictions)
#     max_val = np.max(aggregated_predictions)
#     ranked_predictions = min_val + (max_val - min_val) * (average_ranks / len(data))
#
#     aggregated_result = {
#         "request_id": req_id,
#         "prediction": ranked_predictions.tolist(),
#         "pipeline_id": ",".join(pipeline_ids),
#         "inference_model_id": ",".join(inference_model_ids),
#     }
#
#     return aggregated_result
#
#
# # ---------------------------------------------------------
#
#
# def majority_voting(data: list) -> Union[dict, None]:
#     if len(data) < 2:
#         qoa_logger.error("No aggregation needed for only one prediction")
#         return None
#
#     req_id = data[0]["request_id"]
#
#     all_predictions = []
#     pipeline_ids = []
#     inference_model_ids = []
#
#     for entry in data:
#         all_predictions.append(entry["prediction"])
#         pipeline_ids.append(entry["pipeline_id"])
#         inference_model_ids.append(entry["inference_model_id"])
#
#     # Assumes predictions are class labels
#     majority_vote = [
#         max(set(predictions), key=predictions.count)
#         for predictions in zip(*all_predictions, strict=True)
#     ]
#
#     aggregated_result = {
#         "request_id": req_id,
#         "prediction": majority_vote,
#         "pipeline_id": ",".join(pipeline_ids),
#         "inference_model_id": ",".join(inference_model_ids),
#     }
#
#     return aggregated_result
#
#
# # more functions
# def median_averaging(data: list) -> Union[dict, None]:
#     if len(data) < 2:
#         qoa_logger.error("No aggregation needed for only one prediction")
#         return None
#
#     req_id = data[0]["request_id"]
#     aggregated_predictions = []
#     pipeline_ids = []
#     inference_model_ids = []
#
#     for entry in data:
#         aggregated_predictions.append(entry["prediction"])
#         pipeline_ids.append(entry["pipeline_id"])
#         inference_model_ids.append(entry["inference_model_id"])
#
#     median_prediction = np.median(aggregated_predictions, axis=0)
#
#     aggregated_result = {
#         "request_id": req_id,
#         "prediction": median_prediction.tolist(),
#         "pipeline_id": ",".join(pipeline_ids),
#         "inference_model_id": ",".join(inference_model_ids),
#     }
#
#     return aggregated_result

import os
import logging
import pickle
import json
import numpy
from sklearn.externals import joblib
from sklearn.linear_model import Ridge


def init():
    global model
    # AZUREML_MODEL_DIR is an environment variable created during deployment.
    # It is the path to the model folder (./azureml-models/$MODEL_NAME/$VERSION)
    # For multiple models, it points to the folder containing all deployed models (./azureml-models)
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR"), "sklearn_regression_model.pkl")
    # deserialize the model file back into a sklearn model
    model = joblib.load(model_path)


# note you can pass in multiple rows for scoring
def run(raw_data):
    try:
        logging.info("request received")
        data = json.loads(raw_data)["data"]
        data = numpy.array(data)
        model.predict(data)
        # return a hardcoded probability
        return [0.5, 0.5]
        # return result.tolist()
    except Exception as e:
        error = str(e)
        return error

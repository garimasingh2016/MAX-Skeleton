#
# Copyright 2018-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from core.model import ModelWrapper
from maxfw.core import MAX_API, PredictAPI
from flask_restplus import fields
from werkzeug.datastructures import FileStorage
import tensorflow as tf
import json


# Set up parser for input data
# (http://flask-restplus.readthedocs.io/en/stable/parsing.html)
input_parser = MAX_API.parser()
# Example parser for file input
input_parser.add_argument('file', type=FileStorage,
                          location='files', required=True)


# Creating a JSON response model:
# https://flask-restplus.readthedocs.io/en/stable/marshalling.html#the-api-model-factory
text_answer = MAX_API.model('TextAnswer', {
    'question_id': fields.String(required=False, description='Question identifier'),
    'question': fields.String(required=False, description='Question text.'),
    'answer': fields.String(required=True, description='Text answer to question'),
})

predict_response = MAX_API.model('ModelPredictResponse', {
    'status': fields.String(required=True, description='Response status message'),
    'predictions': fields.List(fields.Nested(text_answer), description='Predicted answers to questions')
})


class ModelPredictAPI(PredictAPI):

    model_wrapper = ModelWrapper()

    @MAX_API.doc('predict')
    @MAX_API.expect(input_parser)
    @MAX_API.marshal_with(predict_response)
    def post(self):
        """Make a prediction given input data"""
        result = {'status': 'error'}

        args = input_parser.parse_args()
        input_data = json.load(args['file'])["data"]
        # input_data = input_file.read()
        preds = self.model_wrapper.predict(input_data)
        # Modify this code if the schema is changed
        answers = [{'question_id': p, 'question': preds[p][0], 'answer': preds[p][1]}
                   for p in preds]
        result['predictions'] = answers
        result['status'] = 'ok'

        return result

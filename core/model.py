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

from maxfw.model import MAXModelWrapper

import logging
from config import DEFAULT_MODEL_PATH
from core.run_squad import MAXAPIProcessor, read_squad_examples, convert_examples_to_features
from core.tokenization import FullTokenizer
import tensorflow as tf
from tensorflow.python.saved_model import tag_constants

logger = logging.getLogger()


class ModelWrapper(MAXModelWrapper):

    MODEL_META_DATA = {
        'id': 'ID',
        'name': 'MODEL NAME',
        'description': 'DESCRIPTION',
        'type': 'MODEL TYPE',
        'source': 'MODEL SOURCE',
        'license': 'LICENSE'
    }

    def __init__(self, path=DEFAULT_MODEL_PATH):
        logger.info('Loading model from: {}...'.format(path))

        # Parameters for inference
        self.max_seq_length = 384
        self.doc_stride = 128
        self.max_query_length = 64

        # Loading the tf Graph
        self.graph = tf.Graph()
        self.sess = tf.Session(graph=self.graph)
        tf.saved_model.loader.load(
            self.sess, [tag_constants.SERVING], DEFAULT_MODEL_PATH)

        # Initialize the dataprocessor
        self.processor = MAXAPIProcessor()

        # Initialize the tokenizer
        self.tokenizer = FullTokenizer(
            vocab_file='core/vocab.txt', do_lower_case=True)

        logger.info('Loaded model')

    def _pre_process(self, inp):
        return inp

    def _post_process(self, result):
        return result

    def _predict(self, x, batch_size=32):
        predict_examples = read_squad_examples(x)

        # Input and output tensors
        input_ids = self.sess.graph.get_tensor_by_name('input_ids_1:0')
        input_mask = self.sess.graph.get_tensor_by_name('input_mask_1:0')
        unique_ids = self.sess.graph.get_tensor_by_name('unique_ids_1:0')
        segment_ids = self.sess.graph.get_tensor_by_name('segment_ids_1:0')
        outputs = self.sess.graph.get_tensor_by_name('loss/Softmax:0')

        predictions = []

        for i in range(0, len(predict_examples), batch_size):
            features = convert_examples_to_features(predict_examples[
                                                    i:i + batch_size], self.tokenizer, self.max_seq_length, self.doc_stride, self.max_query_length)

            feed_dict = {}
            feed_dict[input_ids] = []
            feed_dict[input_mask] = []
            feed_dict[unique_ids] = []
            feed_dict[segment_ids] = []
            for feature in features:
                feed_dict[input_ids].append(feature.input_ids)
                feed_dict[input_mask].append(feature.input_mask)
                feed_dict[label_ids].append(feature.label_ids)
                feed_dict[unique_ids].append(features.unique_ids)

            result = self.sess.run(outputs, feed_dict=feed_dict)

            predictions.append(list(p) for p in result)

        return predictions

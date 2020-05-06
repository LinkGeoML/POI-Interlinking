# -*- coding: utf-8 -*-
# Author: vkaff
# E-mail: vkaffes@imis.athena-innovation.gr

import time
import os
from sklearn.model_selection import train_test_split

from poi_interlinking import config
from poi_interlinking.learning import hyperparam_tuning
from poi_interlinking.helpers import StaticValues
from poi_interlinking.processing.features import Features
from poi_interlinking.processing.sim_measures import LGMSimVars


class StrategyEvaluator:
    """
    This class implements the pipeline for various strategies.
    """
    def __init__(self, encoding='latin'):
        self.encoding = encoding

    def hyperparamTuning(self, train_data, test_data):
        """A complete process of distinct steps in figuring out the best ML algorithm with best hyperparameters to
        toponym interlinking problem.

        :param train_data: Relative path to the train dataset.
        :type train_data: str
        :param test_data: Relative path to the test dataset.
        :type test_data: str
        """
        tot_time = time.time()

        LGMSimVars.per_metric_optValues = StaticValues.opt_values[self.encoding.lower()]
        assert (os.path.isfile(os.path.join(config.default_data_path, train_data))), \
            f'{train_data} dataset does not exist'
        assert (os.path.isfile(os.path.join(config.default_data_path, test_data))), \
            f'{test_data} dataset does not exist'

        f = Features()
        pt = hyperparam_tuning.ParamTuning()

        start_time = time.time()
        f.load_data(os.path.join(config.default_data_path, train_data), self.encoding)
        fX, y = f.build()
        print("Loaded train dataset and build features for {} setup; {} sec.".format(
            config.MLConf.classification_method, time.time() - start_time))

        start_time = time.time()
        # 1st phase: find out best classifier from a list of candidate ones
        best_clf = pt.fineTuneClassifiers(fX, y)
        print("Best classifier {} with hyperparams {} and score {}; {} sec.".format(
            best_clf['classifier'], best_clf['hyperparams'], best_clf['score'], time.time() - start_time)
        )

        start_time = time.time()
        # 2nd phase: train the fine tuned best classifier on the whole train dataset (no folds)
        estimator = pt.trainClassifier(fX, y, best_clf['estimator'])
        print("Finished training model on the dataset; {} sec.".format(time.time() - start_time))

        start_time = time.time()
        f.load_data(os.path.join(config.default_data_path, test_data), self.encoding)
        fX, y = f.build()
        print("Loaded test dataset and build features; {} sec".format(time.time() - start_time))

        start_time = time.time()
        # 3th phase: test the fine tuned best classifier on the test dataset
        metrics = pt.testClassifier(fX, y, estimator)
        self._print_stats({
            'classifier': best_clf['classifier'],
            **metrics,
            'time': start_time
        })

        print("The whole process took {} sec.".format(time.time() - tot_time))

    def evaluate(self, dataset):
        """Train and evaluate selected ML algorithms with custom hyper-parameters on dataset.
        """
        tot_time = time.time()

        LGMSimVars.per_metric_optValues = StaticValues.opt_values[self.encoding.lower()]
        assert (os.path.isfile(os.path.join(config.default_data_path, dataset))), \
            f'{os.path.join(config.default_data_path, dataset)} dataset does not exist!!!'

        f = Features()
        pt = hyperparam_tuning.ParamTuning()

        start_time = time.time()
        f.load_data(os.path.join(config.default_data_path, dataset), self.encoding)
        fX, y = f.build()
        print("Loaded dataset and build features for {} setup; {} sec.".format(
            config.MLConf.classification_method, time.time() - start_time))

        fX_train, fX_test, y_train, y_test = train_test_split(
            fX, y, stratify=y, test_size=0.2, random_state=config.seed_no)

        for clf in config.MLConf.clf_custom_params:
            print('Method {}'.format(clf))
            print('=======', end='')
            print(len(clf) * '=')

            start_time = time.time()
            # 1st phase: train each classifier on the whole train dataset (no folds)
            estimator = pt.clf_names[clf][0](**config.MLConf.clf_custom_params[clf])
            estimator = pt.trainClassifier(fX_train, y_train, estimator)
            print("Finished training model on dataset; {} sec.".format(time.time() - start_time))

            start_time = time.time()
            # 2nd phase: test each classifier on the test dataset
            metrics = pt.testClassifier(fX_test, y_test, estimator)
            self._print_stats({
                'classifier': clf,
                **metrics,
                'time': start_time
            })

        print("The whole process took {} sec.\n".format(time.time() - tot_time))

    @staticmethod
    def _print_stats(params):
        print("| Method\t& Accuracy\t& Precision\t& Prec-weighted\t& Recall\t& Rec-weighted"
              "\t& F1-Score\t& F1-weighted\t& Time (sec)")
        print("||{}\t& {}\t& {}\t& {}\t& {}\t& {}\t& {}\t& {}\t& {}".format(
            params['classifier'],
            params['accuracy'],
            params['precision'], params['precision_weighted'],
            params['recall'], params['recall_weighted'],
            params['f1_score'], params['f1_score_weighted'],
            time.time() - params['time']))

        # if params['feature_importances'] is not None:
        #     importances = np.ma.masked_equal(params['feature_importances'], 0.0)
        #     if importances.mask is np.ma.nomask: importances.mask = np.zeros(importances.shape, dtype=bool)
        #
        #     indices = np.argsort(importances.compressed())[::-1][
        #               :min(importances.compressed().shape[0], self.max_features_toshow)]
        #     headers = ["name", "score"]
        #
        #     fcols = StaticValues.featureCols if config.MLConf.extra_features is False \
        #         else StaticValues.featureCols + StaticValues.extra_featureCols
        #     print(tabulate(zip(
        #         np.asarray(fcols, object)[~importances.mask][indices], importances.compressed()[indices]
        #     ), headers, tablefmt="simple"))

        print()

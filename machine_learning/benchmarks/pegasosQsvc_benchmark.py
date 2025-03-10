# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
"""Pegasos Quantum Support Vector Classifier benchmarks."""
import pickle
from itertools import product
from timeit import timeit
from typing import Optional, Union
from qiskit_machine_learning.kernels import QuantumKernel

import numpy as np
from qiskit.algorithms.optimizers import COBYLA
from qiskit_machine_learning.algorithms import PegasosQSVC
from sklearn.metrics import precision_score, recall_score, f1_score
from sympy import evaluate

from .base_classifier_benchmark import DATASET_SYNTHETIC_CLASSIFICATION, DATASET_IRIS_CLASSIFICATION
from .pegasosQsvc_base_benchmark import PegasosQsvcBaseClassifierBenchmark


class PegasosQsvcBenchmarks(PegasosQsvcBaseClassifierBenchmark):
    """Pegasos Quantum Support Vector Classifier benchmarks."""

    version = 1
    timeout = 1200.0
    params = [
        # Only one dataset now 
        [DATASET_SYNTHETIC_CLASSIFICATION],
        ["qasm_simulator", "statevector_simulator"]
    ]
    param_names = ["dataset", "backend"]

    def __init__(self) -> None:
        super().__init__()
        self.train_features: Optional[np.ndarray] = None
        self.train_labels: Optional[np.ndarray] = None
        self.test_features: Optional[np.ndarray] = None
        self.test_labels: Optional[np.ndarray] = None
        self.model: Optional[QuantumKernel] = None 

    def setup(self, dataset: str, quantum_instance_name: str) -> None:
        """Set up the benchmark."""
        self.train_features = self.datasets[dataset]["train_features"]
        self.train_labels = self.datasets[dataset]["train_labels"]
        self.test_features = self.datasets[dataset]["test_features"]
        self.test_labels = self.datasets[dataset]["test_labels"]

        n_qubits = self.train_features.shape[1]
        if dataset == DATASET_SYNTHETIC_CLASSIFICATION:
            _kernel = self._construct_QuantumKernel_classical_classifier(quantum_instance_name= quantum_instance_name, 
                                                                            num_qubits = n_qubits) #this is just a kernel matrix
            model = PegasosQSVC(kernel = _kernel.evaluate)
           
        elif dataset == DATASET_IRIS_CLASSIFICATION:
            _kernel = self._construct_QuantumKernel_classical_classifier(quantum_instance_name= quantum_instance_name, 
                                                                            num_qubits = n_qubits) #this is just a kernel matrix
            model = PegasosQSVC(kernel = _kernel.evaluate)
            
        else:
            raise ValueError(f"Unsupported dataset: {dataset}")
            
        file_name = f"PegasosQsvc_{dataset}_{quantum_instance_name}.pickle"
        with open(file_name, "rb") as file:
            self.result = pickle.load(file)
            
    def setup_cache(self) -> None:
        """Cache PegasosQsvc fitted model."""
        for dataset, backend in product(*self.params):
            train_features = self.datasets[dataset]["train_features"]
            train_labels = self.datasets[dataset]["train_labels"]
            #for now I put only 1 optimizer as they do, but this is fishy
            n_qubits = train_features.shape[1]
            
            #create model based on params
            #for now I directly create the classifier (so add svc in the quantum kernel method)
            if dataset == DATASET_SYNTHETIC_CLASSIFICATION:
                _kernel = self._construct_QuantumKernel_classical_classifier(quantum_instance_name= backend, 
                                                                             optimizer = COBYLA(maxiter=200), 
                                                                             num_qubits = n_qubits)
                model = PegasosQSVC(kernel = _kernel.evaluate)
                
            elif dataset == DATASET_IRIS_CLASSIFICATION:
                _kernel = self._construct_QuantumKernel_classical_classifier(quantum_instance_name= backend, 
                                                                             optimizer = COBYLA(maxiter=200), 
                                                                             num_qubits = n_qubits)
                model = PegasosQSVC(kernel = _kernel.evaluate)
            else:
                raise ValueError(f"Unsupported dataset: {dataset}")              
          
            result = model.fit(train_features, train_labels)
            file_name = f"PegasosQsvc_{dataset}_{backend}.pickle"
            with open(file_name, "wb") as file:
                pickle.dump(result, file)  

    # pylint: disable=invalid-name
    def time_score_PegasosQsvc_classifier(self, _, __):
        """Time scoring PegasosQsvc on data."""
        self.model.score(self.train_features, self.train_labels)

    def time_predict_PegasosQsvc_classifier(self, _, __):
        """Time predicting with PegasosQsvc."""
        self.model.predict(self.train_features)

    def track_accuracy_score_PegasosQsvc_classifier(self, _, __):
        """Tracks the overall accuracy of the classification results."""
        return self.model.score(self.test_features, self.test_labels)

    def track_precision_score_PegasosQsvc_classifier(self, _, __):
        """Tracks the precision score."""
        predicts = self.model.predict(self.test_features)
        return precision_score(y_true=self.test_labels, y_pred=predicts, average="micro")

    def track_recall_score_PegasosQsvc_classifier(self, _, __):
        """Tracks the recall score for each class of the classification results."""
        predicts = self.model.predict(self.test_features)
        return recall_score(y_true=self.test_labels, y_pred=predicts, average="micro")

    def track_f1_score_PegasosQsvc_classifier(self, _, __):
        """Tracks the f1 score for each class of the classification results."""
        predicts = self.model.predict(self.test_features)
        return f1_score(y_true=self.test_labels, y_pred=predicts, average="micro")

if __name__ == "__main__":
    bench = PegasosQsvcBenchmarks()
    bench.setup_cache()
    for dataset_name, backend_name in product(*PegasosQsvcBenchmarks.params):
        try:
            bench.setup(dataset_name, backend_name)
        except NotImplementedError:
            continue

        for method in (
            "time_score_PegasosQsvc_classifier",
            "time_predict_PegasosQsvc_classifier",
            "track_accuracy_score_PegasosQsvc_classifier",
            "track_precision_score_PegasosQsvc_classifier",
            "track_recall_score_PegasosQsvc_classifier",
            "track_f1_score_PegasosQsvc_classifier",
        ):
            elapsed = timeit(
                f'bench.{method}("{dataset_name}", "{backend_name}")', number=10, globals=globals()
            )
            
            print(f"{method}:\t{elapsed}")

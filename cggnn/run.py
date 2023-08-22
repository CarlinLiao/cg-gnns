"""Run through the entire SPT CG-GNN pipeline."""

from os import makedirs
from shutil import rmtree
from typing import Dict, Tuple, List, Literal, Optional

from pandas import DataFrame
from dgl import DGLGraph

from cggnn.util.constants import TRAIN_VALIDATION_TEST
from cggnn.generate_graphs import generate_graphs
from cggnn.train import train
from cggnn.explain import explain_cell_graphs


def run(df_cell: DataFrame,
        df_label: DataFrame,
        label_to_result: Dict[int, str],
        channel_symbols_by_column_name: Dict[str, str],
        phenotype_symbols_by_column_name: Dict[str, str],
        validation_data_percent: int = 15,
        test_data_percent: int = 15,
        roi_side_length: int = 600,
        target_column: Optional[str] = None,
        batch_size: int = 1,
        epochs: int = 10,
        learning_rate: float = 10e-3,
        k_folds: int = 0,
        explainer: str = 'pp',
        merge_rois: bool = True,
        prune_misclassified: bool = True
        ) -> None:
    """Run the SPT CG-GNN pipeline on the given DataFrames and identifier-to-name dictionaries."""
    makedirs('tmp/', exist_ok=True)
    graphs = generate_graphs(df_cell, df_label, validation_data_percent,
                             test_data_percent, roi_side_length, target_column)

    train_validation_test: Tuple[Tuple[List[DGLGraph], List[int]],
                                 Tuple[List[DGLGraph], List[int]],
                                 Tuple[List[DGLGraph], List[int]]] = (([], []), ([], []), ([], []))
    for graph_datum in graphs:
        i_set: Literal[0, 1, 2] = 0
        if graph_datum.train_validation_test == 'validation':
            i_set = 1
        elif graph_datum.train_validation_test == 'test':
            i_set = 2
        train_validation_test[i_set][0].append(graph_datum.graph)
        train_validation_test[i_set][1].append(graph_datum.label)
    model = train(train_validation_test, 'tmp/', epochs=epochs,
                  learning_rate=learning_rate, batch_size=batch_size, k_folds=k_folds)

    columns = df_cell.columns.values
    i = -1
    while len(train_validation_test[i][0]) == 0:
        i -= 1
        if i < -3:
            raise RuntimeError('all sets created are empty')
    evaluation_set = train_validation_test[i]
    assert evaluation_set is not None
    explanations = explain_cell_graphs(
        graphs, model, explainer,
        [channel_symbols_by_column_name[col] for col in columns if col.startswith('F')],
        [phenotype_symbols_by_column_name[col] for col in columns if col.startswith('P')],
        merge_rois=merge_rois,
        prune_misclassified=prune_misclassified,
        cell_graph_names=[d.name for d in graphs
                          if d.train_validation_test == TRAIN_VALIDATION_TEST[i]],
        label_to_result=label_to_result,
        out_directory='out/')

    explanations[0].to_csv('out/separability_concept.csv')
    explanations[1].to_csv('out/separability_attribute.csv')
    for class_pair, df in explanations[2].items():
        df.to_csv(f'out/separability_k_best_{class_pair}.csv')
    rmtree('tmp/')

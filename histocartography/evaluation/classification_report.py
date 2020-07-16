import torch
from sklearn.metrics.classification import classification_report


class ClassificationReport:

    def __init__(self):
        """
        Classification report constructor
        """

    def __call__(self, logits, labels, class_name=None):
        """
        Compute classification report using the labels and logits
        :param labels: (list of torch.LongTensor)
        :param logits: (list of torch.FloatTensor)
        :return: report (dict)
        """

        # get predictions
        predictions = torch.argmax(logits, dim=1)

        # get classification report
        report = classification_report(
            y_true=labels.cpu().numpy(),
            y_pred=predictions.cpu().numpy(),
            output_dict=True,
            target_names=class_name
        )

        return report

class PerClassWeightedF1Score:
    def __init__(self):
        """
        Per class weighted f1 score constructor
        """
        self.eval_classification_report = ClassificationReport()

    def __call__(self, logits, labels, class_split='benignVSpathologicalbenignVSudhVSadhVSfeaVSdcisVSmalignant'):
        """
        Compute per class weighted f1 score
        :param labels: (list of torch.LongTensor)
        :param logits: (list of torch.FloatTensor)
        :return: per class weighted f1 score (dict)
        """

        # get predictions
        class_name = class_split.split('VS')
        classification_report = self.eval_classification_report(logits, labels, class_name)
        per_class_weighted_f1_score = {key: round(val['f1-score'], 3) for key, val in classification_report.items()}

        del per_class_weighted_f1_score['micro avg']
        del per_class_weighted_f1_score['macro avg']
        del per_class_weighted_f1_score['weighted avg']

        return per_class_weighted_f1_score


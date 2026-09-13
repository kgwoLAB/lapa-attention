from collections import Counter


def field_counts(truth, predictions):
    def key(f):
        return f["start"], f["end"], f["semantic"]
    gold, guessed = Counter(map(key, truth)), Counter(map(key, predictions))
    tp = sum((gold & guessed).values())
    return tp, sum(guessed.values()) - tp, sum(gold.values()) - tp


def field_metrics(counts):
    tp, fp, fn = counts
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}

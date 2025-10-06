from app.evaluation.metrics_util import ndcg_at_k, recall_at_k

def test_ndcg_recall_example():
    # ideal: [2,3,1,0,0,0] gibi düşün; sistem sırası: ilk 5'te iyi olmalı
    rel = [2,3,1,0,0,0]
    ndcg5 = ndcg_at_k(rel, 5)
    assert 0.8 <= ndcg5 <= 1.0

    bin_rel = [1,1,1,0,0,0]
    r5 = recall_at_k(bin_rel, 5)
    assert r5 == 1.0

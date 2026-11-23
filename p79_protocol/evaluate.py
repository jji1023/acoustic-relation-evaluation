"""Integer-count metrics for semantic answers and matched factorial edges."""

from collections import Counter

from .questions import CONDITIONS, FACTORS


def _validate_labels(gt, *answers):
    if gt not in ("A", "B") or any(answer not in ("A", "B", None) for answer in answers):
        raise ValueError("Expected semantic GT A/B and semantic answers A/B or None")


def count_endpoints(pairs):
    result = Counter()
    for gt, ab, ba in pairs:
        _validate_labels(gt, ab, ba)
        both = ab is not None and ba is not None
        result["pairs"] += 1
        result["endpoints"] += 2
        result["valid"] += int(ab is not None) + int(ba is not None)
        result["correct"] += int(ab == gt) + int(ba == gt)
        result["both_valid"] += int(both)
        result["agreement"] += int(both and ab == ba)
    return result


def cube_edges():
    for index, factor in enumerate(FACTORS):
        for bits in CONDITIONS:
            if bits[index] == "0":
                yield factor, bits, bits[:index] + "1" + bits[index + 1:]


def edge_outcome(left, right):
    """Each endpoint is (semantic GT, parsed semantic identity or None)."""
    left_gt, first = left
    right_gt, last = right
    _validate_labels(left_gt, first)
    _validate_labels(right_gt, last)
    valid_pair = first is not None and last is not None
    joint = first == left_gt and last == right_gt
    flip = valid_pair and first != last
    same = valid_pair and first == last
    return dict(joint=int(joint), both_valid=int(valid_pair), flip=int(flip), same=int(same))


def count_ir(edge_rows):
    cells = {}
    for question, intervention, left, right in edge_rows:
        key = (question, intervention)
        if key[0] not in FACTORS or key[1] not in FACTORS:
            raise ValueError("Invalid factor or intervention")
        if (left[0] != right[0]) != (question == intervention):
            raise ValueError("Edge GT polarity conflicts with its intervention type")
        cell = cells.setdefault(key, Counter())
        cell["edges"] += 1
        cell.update(edge_outcome(left, right))
    return cells


def strict_four_answer(left, right):
    """Each scene contains (GT, AB answer, BA answer)."""
    _validate_labels(*left)
    _validate_labels(*right)
    return int(all(gt == ab == ba for gt, ab, ba in (left, right)))

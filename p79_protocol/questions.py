"""Generate factorial QA keys and illustrative, model-independent prompts."""

from itertools import product

from .audio import relation_roles
from .parser import sound_name_keys


FACTORS = ("POSITION", "DURATION", "LEVEL")
CONDITIONS = tuple("".join(bits) for bits in product("01", repeat=3))
STEMS = dict(zip(FACTORS, ("Which sound starts earlier?", "Which sound lasts longer?",
                           "Which sound has the higher level?")))


def question_rows(scene_group, names):
    if set(names) != {"A", "B"}:
        raise ValueError("Expected names for semantic roles A and B")
    sound_name_keys((names["A"], names["B"]))
    for bits in CONDITIONS:
        for factor, gt in zip(FACTORS, relation_roles(bits)):
            for order in ("AB", "BA"):
                yield dict(qa_id=f"{scene_group}/{bits}/{factor}/{order}", condition=bits,
                           factor=factor, order=order, gt=gt, options=tuple(names[r] for r in order))


def illustrative_prompt(row, interface):
    if interface not in {"SOUND", "LETTER"}:
        raise ValueError("Unknown interface")
    first, second = row["options"]
    if row["factor"] not in STEMS:
        raise ValueError("Unknown question factor")
    instruction = ("Return the sound name only." if interface == "SOUND"
                   else "Return the option letter only.")
    return f"{STEMS[row['factor']]}\nA. {first}\nB. {second}\n{instruction}"

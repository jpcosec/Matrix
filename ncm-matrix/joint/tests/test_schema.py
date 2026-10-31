"""SPEC §2: validation and separation of inputs from supervision."""
import dataclasses

import pytest
import torch

from joint.model import collate
from joint.schema import Mention, Query, Record, Supervision, model_inputs, validate


def record(text="El banco cerró.", mentions=(Mention("m0", 3, 8),), queries=(Query("q0", "m0", "https://x/r", "https://x/o"),)):
    return Record("e", "g", text, (), tuple(mentions), tuple(queries), Supervision("ctx", ()))


def test_valid_record_passes():
    validate(record())


@pytest.mark.parametrize("mentions", [(Mention("m0", 3, 7),), (Mention("m0", 0, 99),), (Mention("m0", 2, 8),)])
def test_misaligned_or_out_of_range_spans_are_rejected(mentions):
    with pytest.raises(ValueError):
        validate(record(mentions=mentions))


def test_too_long_fragments_are_rejected_not_truncated():
    with pytest.raises(ValueError, match="exceed"):
        validate(record(text="a " * 70 + "banco", mentions=(Mention("m0", 140, 145),)))


def test_dangling_query_endpoint_is_rejected():
    with pytest.raises(ValueError, match="neither mention nor URI"):
        validate(record(queries=(Query("q0", "m9", "https://x/r", "https://x/o"),)))


def test_model_inputs_carry_no_supervision_or_ids(small):
    records, _ = small
    inputs = model_inputs(records[0])
    assert {f.name for f in dataclasses.fields(inputs)} == {"text", "observed_context", "mention_spans", "query_structure"}
    assert records[0].example_id not in repr(inputs) and records[0].source_group not in repr(inputs)


def test_changing_supervision_does_not_change_encoder_inputs(trainer, small):
    records, _ = small
    original = records[:4]
    flipped = [dataclasses.replace(r, supervision=Supervision("other", ())) for r in original]
    a, b = collate(original, trainer.vocab), collate(flipped, trainer.vocab)
    assert all(torch.equal(a[k], b[k]) for k in a)

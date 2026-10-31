import pytest

from joint.fixture import build_records
from joint.train import Trainer, TrainConfig

SMALL = {"train": 12, "validation": 2, "test_entity": 2, "test_combination": 2}


@pytest.fixture(scope="session")
def small():
    return build_records(seed=3, groups=SMALL)


@pytest.fixture(scope="session")
def full_fixture():
    return build_records()


def make_trainer(small, **overrides) -> Trainer:
    records, worlds = small
    cfg = TrainConfig(seed=7, steps=10, batch_groups=2, device="cpu", asi_every=10**6)
    for key, value in overrides.items():
        setattr(cfg, key, value)
    return Trainer(cfg, records, worlds)


@pytest.fixture
def trainer(small):
    return make_trainer(small)


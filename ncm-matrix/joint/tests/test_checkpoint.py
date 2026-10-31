"""SPEC §9.1: a checkpoint holds everything needed to resume the very next step."""
import torch

from joint.train import Trainer
from .conftest import make_trainer


def test_checkpoint_resumes_the_next_step_exactly(small, tmp_path):
    trainer = make_trainer(small, asi_every=3)
    for _ in range(4):
        trainer.train_step()
    path = tmp_path / "ckpt.pt"
    trainer.save(path)
    state = torch.load(path, weights_only=False)
    for key in ("model", "optimizer", "step", "config", "vocabulary", "reservoir", "proposals", "rng"):
        assert key in state
    assert any("ema_w_" in k for k in state["model"])
    assert state["proposals"], "ASI proposals are part of the checkpoint"
    continued = trainer.train_step()
    resumed = Trainer.load(path, *small, device="cpu")
    again = resumed.train_step()
    assert resumed.step == continued["step"] == again["step"]
    assert abs(continued["loss"] - again["loss"]) < 1e-5

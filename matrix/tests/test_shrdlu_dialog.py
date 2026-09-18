from prototypes.shrdlu.lowering import PrototypeHarness


def test_pronoun_it_uses_last_referent() -> None:
    harness = PrototypeHarness()
    harness.execute("Put the red block on the blue cube.")

    result = harness.execute("Is it on the blue cube?")

    assert result.status == "accept"
    assert result.payload["truth"] == "true"


def test_ambiguous_pronoun_without_history_returns_ambiguous() -> None:
    harness = PrototypeHarness()

    result = harness.execute("Is it on the blue cube?")

    assert result.status == "ambiguous"
    assert result.reason == "prototype referent is unresolved"

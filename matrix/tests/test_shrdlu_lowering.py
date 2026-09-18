from prototypes.shrdlu.lowering import PrototypeHarness


def test_prototype_can_lower_and_execute_put_command() -> None:
    harness = PrototypeHarness()

    result = harness.execute("Put the red block on the blue cube.")

    assert result.status == "accept"
    assert result.payload["wigame_id"] == "wigame:scene"
    assert result.payload["proposition"] == "(on red-block blue-cube)"


def test_prototype_can_answer_truth_query_against_runtime() -> None:
    harness = PrototypeHarness()
    harness.execute("Put the red block on the blue cube.")

    result = harness.execute("Is the red block on the blue cube?")

    assert result.status == "accept"
    assert result.payload["truth"] == "true"

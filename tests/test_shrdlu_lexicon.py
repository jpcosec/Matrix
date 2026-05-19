from src.operational_model import build_shrdlu_lexicon


def test_multiword_combination_collapses_to_one_token() -> None:
    lexicon = build_shrdlu_lexicon()

    tokens = lexicon.tokenize("Pick up the red block on top of the box.")

    assert [token.root for token in tokens] == [
        "pick-up",
        "the",
        "red",
        "block",
        "on-top-of",
        "the",
        "box",
    ]


def test_irregular_and_plural_forms_normalize_to_roots() -> None:
    lexicon = build_shrdlu_lexicon()

    tokens = lexicon.tokenize("Are the boxes under the pyramids?")

    assert [token.root for token in tokens] == [
        "be",
        "the",
        "box",
        "under",
        "the",
        "pyramid",
    ]


def test_unknown_words_become_name_tokens() -> None:
    lexicon = build_shrdlu_lexicon()

    tokens = lexicon.tokenize("Move laika onto the box.")

    assert tokens[1].root == "laika"
    assert "name" in tokens[1].categories

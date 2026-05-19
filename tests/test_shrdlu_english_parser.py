from src.operational_model import ParseError, build_shrdlu_lexicon, parse_controlled_english


def test_parse_imperative_put_sentence() -> None:
    frame = parse_controlled_english("Put the red block on the blue cube.")

    assert frame.to_sexpr() == (
        "(command put (entity (det def) (adj red) (noun block)) "
        "(relation on (entity (det def) (adj blue) (noun cube))))"
    )


def test_parse_imperative_pick_up_combination() -> None:
    frame = parse_controlled_english("Pick up the green pyramid.")

    assert frame.to_sexpr() == "(command pick-up (entity (det def) (adj green) (noun pyramid)))"


def test_parse_yes_no_question() -> None:
    frame = parse_controlled_english("Is the red block under the box?")

    assert frame.to_sexpr() == (
        "(query truth (subject (entity (det def) (adj red) (noun block))) "
        "(relation under) (object (entity (det def) (noun box))))"
    )


def test_parse_what_question() -> None:
    frame = parse_controlled_english("What is on the blue block?")

    assert frame.to_sexpr() == (
        "(query which-entity (wh what) (relation on) "
        "(object (entity (det def) (adj blue) (noun block))))"
    )


def test_parse_which_question() -> None:
    frame = parse_controlled_english("Which red block is on the table?")

    assert frame.to_sexpr() == (
        "(query which-entity (wh which) (subject (entity (adj red) (noun block))) "
        "(relation on) (object (entity (det def) (noun table))))"
    )


def test_parse_where_question() -> None:
    frame = parse_controlled_english("Where is the red block?")

    assert frame.to_sexpr() == (
        "(query where (wh where) (subject (entity (det def) (adj red) (noun block))))"
    )


def test_parser_rejects_unsupported_shape() -> None:
    lexicon = build_shrdlu_lexicon()

    try:
        parse_controlled_english("Thanks.", lexicon=lexicon)
    except ParseError as exc:
        assert "unsupported sentence start" in str(exc)
    else:
        raise AssertionError("expected ParseError")

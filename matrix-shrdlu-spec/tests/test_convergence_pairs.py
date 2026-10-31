"""Tests for pair-based convergence: intensity, batching and memory."""

from __future__ import annotations

import tracemalloc
from time import perf_counter

import numpy as np
import pytest

from pipeline.convergence import (
    _configuration_matrix,
    _configurations,
    _pair_scores,
    converge_in_batches,
    symbol_convergence,
)
from pipeline.decompose import Declaration, decompose
from populator import build_contexts
from sia.contingency import contingency
from sia.intensity import phi_classical
from tests.fixtures.curie_franklin import generate


@pytest.fixture(scope="module")
def synthetic():
    documents = generate(0)
    contexts = build_contexts(documents, lang="en")
    declarations = [declaration for context in contexts for declaration in decompose(context, lang="en")]
    return contexts, declarations


def _variables(declarations: list[Declaration], min_support: int = 2) -> set[str]:
    counts: dict[str, int] = {}
    for declaration in declarations:
        for symbol in (declaration.a, declaration.b):
            counts[symbol] = counts.get(symbol, 0) + 1
    return {symbol for symbol, count in counts.items() if count >= min_support}


def test_pair_intensity_matches_the_dense_measure(synthetic):
    from src.operational_model import LogicalSystem, SExpressionRuntime
    from pipeline.ingest import ingest_contexts

    contexts, declarations = synthetic
    system = LogicalSystem()
    ingest_contexts(system, SExpressionRuntime(system), contexts, declarations)
    variables = _variables(declarations)
    configurations = _configurations(declarations, {}, {}, variables, 2, 1.0)

    scores = _pair_scores(configurations, variables)
    matrix = _configuration_matrix(configurations, scores.symbols)
    dense = phi_classical(contingency(matrix))
    position = {symbol: index for index, symbol in enumerate(scores.symbols)}

    assert scores.rows.size > 0
    for row, column, phi in zip(scores.rows, scores.cols, scores.phi):
        expected = dense[position[scores.symbols[int(row)]], position[scores.symbols[int(column)]]]
        assert abs(float(phi) - float(expected)) < 1e-9


def test_batches_reproduce_the_full_run(synthetic):
    from src.operational_model import LogicalSystem, SExpressionRuntime
    from pipeline.ingest import ingest_contexts

    contexts, declarations = synthetic
    full_system = LogicalSystem()
    ingest_contexts(full_system, SExpressionRuntime(full_system), contexts, declarations)
    full = symbol_convergence(full_system, contexts, declarations, taut_df=1.0)

    batch_system = LogicalSystem()
    ingest_contexts(batch_system, SExpressionRuntime(batch_system), contexts, declarations)
    batched = converge_in_batches(batch_system, contexts, declarations, batch_size=5, taut_df=1.0)

    def partitions(report):
        groups: dict[str, set[str]] = {}
        for symbol, referent in report.referents.items():
            groups.setdefault(referent, set()).add(symbol)
        return {frozenset(group) for group in groups.values()}

    batched_promotions = {(entry["kind"], entry["source"], entry["target"]) for entry in batched.promoted}
    full_promotions = {(entry["kind"], entry["source"], entry["target"]) for entry in full.promoted}

    assert batched.batches == 6
    assert partitions(batched) == partitions(full)
    # The batched run compares each batch against the referents already promoted, so
    # its configuration keys are ref-based earlier than in the one-shot run: some
    # pairs can cross the promotion threshold only in the latter. Everything the
    # batched run promotes, the full run promotes too.
    assert batched_promotions <= full_promotions


def _scale_fixture():
    contexts, declarations = [], []
    for context_index in range(300):
        ctx_id = f"c{context_index:03d}"
        from populator.contexts import Chunk, ContextIndex

        contexts.append(
            ContextIndex(chunk=Chunk(ctx_id=ctx_id, document_id=f"{ctx_id}.md", title="", text="", char_offset=0), sentences=[], signs={})
        )
        for offset in range(10):
            symbol = f"s{context_index * 10 + offset:04d}"
            for config_index in ((context_index * 3 + offset + step) % 1000 for step in range(3)):
                declarations.append(
                    Declaration(
                        ctx_id=ctx_id,
                        relation="r",
                        a=symbol,
                        b=f"obj{config_index:03d}",
                        a_sign=symbol,
                        b_sign=f"obj{config_index:03d}",
                        sentence_index=0,
                        span=(0, 1),
                    )
                )
    return contexts, declarations


def test_scale_stays_small_and_fast():
    from src.operational_model import LogicalSystem, SExpressionRuntime
    from pipeline.ingest import ingest_contexts

    contexts, declarations = _scale_fixture()
    system = LogicalSystem()
    ingest_contexts(system, SExpressionRuntime(system), contexts, declarations)

    tracemalloc.start()
    start = perf_counter()
    report = converge_in_batches(system, contexts, declarations, batch_size=40)
    elapsed = perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert len(report.scores) >= 3000
    assert report.candidates_count > 0
    assert peak < 200 * 1024 * 1024
    assert elapsed < 20.0


def test_continuing_a_report_does_not_duplicate(synthetic):
    from src.operational_model import LogicalSystem, SExpressionRuntime
    from pipeline.ingest import ingest_contexts

    contexts, declarations = synthetic
    system = LogicalSystem()
    ingest_contexts(system, SExpressionRuntime(system), contexts, declarations)

    report = symbol_convergence(system, contexts, declarations, taut_df=1.0)
    promoted = len(report.promoted)
    referents = dict(report.referents)

    again = symbol_convergence(system, contexts, declarations, taut_df=1.0, report=report)

    assert again is report
    assert len(again.promoted) == promoted
    assert again.referents == referents

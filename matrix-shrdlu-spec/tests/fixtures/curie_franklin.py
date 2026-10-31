"""Synthetic corpus: 15 articles about Marie Curie and 15 about Rosalind Franklin.

Each article repeats the same core facts with the subject rotating through the
person's three surface forms, so the same configuration (relation, object) is
declared with different subjects in different contexts: that is what lets the
convergence pass link ``she@curie_i`` with ``marie_curie@curie_j``.
"""

from __future__ import annotations

import random

from populator.extract import Document
from pipeline.decompose import Declaration

CURIE_SUBJECTS = ("Marie Curie", "She", "Curie")
FRANKLIN_SUBJECTS = ("Rosalind Franklin", "She", "Franklin")

# Fifteen core facts per person: five per subject form, so every subject symbol
# takes part in enough configurations to clear the 0.99 promotion threshold.
CURIE_CORE = (
    "{subject} was born in Warsaw.",
    "{subject} was a physicist.",
    "{subject} studied at the Sorbonne.",
    "{subject} won the Nobel Prize.",
    "{subject} worked at Paris.",
    "{subject} discovered polonium.",
    "{subject} discovered radium.",
    "{subject} was a radioactivity pioneer.",
    "{subject} received the Davy Medal.",
    "{subject} taught at the Sorbonne.",
    "{subject} was a Nobel laureate.",
    "{subject} studied at Warsaw.",
)

FRANKLIN_CORE = (
    "{subject} was born in London.",
    "{subject} was a chemist.",
    "{subject} studied at King's College.",
    "{subject} worked at the Cavendish.",
    "{subject} discovered the double helix.",
    "{subject} was a crystallographer.",
    "{subject} discovered the helix structure.",
    "{subject} studied at Newnham College.",
    "{subject} received the Gruber Prize.",
    "{subject} taught at Birkbeck.",
    "{subject} was a biophysicist.",
    "{subject} worked at the Royal Institution.",
)

# Variable facts keep a subject that is *not* one of the person's subject
# symbols, so they do not add counterexamples to that person's convergence.
CURIE_VARIABLES = (
    "The academy awarded the Davy Medal.",
    "The committee praised the radioactivity work.",
    "Some papers signed her as Marie Skłodowska.",
)

FRANKLIN_VARIABLES = (
    "The college awarded the Gruber Prize.",
    "The laboratory used X-ray diffraction.",
    "Some notes describe the helix structure.",
)


def generate(seed: int = 0) -> list[Document]:
    """Returns 15 Curie and 15 Franklin articles with a shared core per person."""

    rng = random.Random(seed)
    documents: list[Document] = [
        Document(f"curie_{index}.md", _curie_article(index, rng)) for index in range(15)
    ]
    documents += [
        Document(f"franklin_{index}.md", _franklin_article(index, rng)) for index in range(15)
    ]
    return documents


def _curie_article(index: int, rng: random.Random) -> str:
    sentences: list[str] = []
    # Each article keeps one surface form, so every subject symbol declares the
    # whole personal core and the three forms converge across articles.
    subject = CURIE_SUBJECTS[(index + 1) % len(CURIE_SUBJECTS)]
    for fact in CURIE_CORE:
        sentences.append(fact.format(subject=subject))
    for _ in range(2):
        sentences.append(rng.choice(CURIE_VARIABLES))
    return "# Marie Curie\n\n" + " ".join(sentences) + "\n"


def _franklin_article(index: int, rng: random.Random) -> str:
    sentences: list[str] = []
    subject = FRANKLIN_SUBJECTS[(index + 2) % len(FRANKLIN_SUBJECTS)]
    for fact in FRANKLIN_CORE:
        sentences.append(fact.format(subject=subject))
    for _ in range(2):
        sentences.append(rng.choice(FRANKLIN_VARIABLES))
    return "# Rosalind Franklin\n\n" + " ".join(sentences) + "\n"


def planted_declarations(seed: int = 0) -> list[Declaration]:
    """Returns ten false facts injected into random contexts."""

    rng = random.Random(seed + 1)
    declarations: list[Declaration] = []
    contexts = [f"curie_{index}" for index in range(15)] + [f"franklin_{index}" for index in range(15)]
    chosen = rng.sample(contexts, 10)
    for number, context in enumerate(chosen):
        declarations.append(
            Declaration(
                ctx_id=context,
                relation="born_in",
                a=f"she@{context}",
                b=f"tokyo_{number}@{context}",
                a_sign="She",
                b_sign=f"Tokyo{number}",
                sentence_index=0,
                span=(0, 1),
                source="heuristic",
            )
        )
    return declarations


planted: list[Declaration] = planted_declarations(0)

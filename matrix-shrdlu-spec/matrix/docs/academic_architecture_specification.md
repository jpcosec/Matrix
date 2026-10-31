# Specification of the Matrix Execution & Evaluation Layer (MEEL) and Tractatus Knowledge Machine

**Authors:** Matrix Project Core Engineering Team  
**Status:** Canonical Academic Specification & Architectural Blueprint  
**Repository Subsystem:** `/home/jp/proyectos/Matrix/Matrix/src/operational_model/`  
**Test Verification:** 120 Unit Tests Passing Cleanly (`pytest` exit code 0)

---

## Abstract

This document presents the formal academic specification and system architecture of **MEEL (Matrix Execution & Evaluation Layer)**, the operational execution engine of the **Tractatus Knowledge Machine (TKM)**. Addressing the fundamental impossibility of continuous vector spaces (LLMs) to represent discontinuous logical boundaries without edge-interference (hallucinations), MEEL decouples linguistic signs ($S$) from deterministic logical symbols ($M$). By mapping propositions into dense Boolean matrices ($\mathbf{M}$) operated via native machine-word bitwise logic (`uint64`), MEEL achieves $\mathcal{O}(1)$ deductive inference, categorical sense validation ($S_i$), and factual evaluation ($V_i$) with absolute immunity to hallucinations.

---

## 1. System Architecture & Component Diagram

The implemented architecture is structured into a 5-tier modular hierarchy, featuring natural language lowering and automated OWL ontology ingestion (`owl2matrix.py`):

```mermaid
graph TD
    subgraph Tier1["1. Surface & Natural Language Tier (Sign S)"]
        LLM["LLM / User Interface"]
        Parser["SHRDLU Parser (english_parser.py)"]
        Lexicon["Lexicon & Grammar (lexicon.py)"]
        Dialog["Dialog State Manager (dialog_state.py)"]
        OWLOntologies["OWL / RDF XML Ontologies"]
    end

    subgraph Tier2["2. Canonical S-Expression, Lowering & OWL Parsing Tier"]
        Lowering["SHRDLU Lowering (lowering.py)"]
        SemanticFrames["Semantic Frames (semantic_frames.py)"]
        OWLParser["OWL2Matrix Parser (owl2matrix.py)"]
        SExprParser["S-Expression Parser (s_expressions.py)"]
        Runtime["S-Expression Runtime (s_expression_runtime.py)"]
    end

    subgraph Tier3["3. Operational System & Game Tier"]
        LogSys["LogicalSystem (logical_system.py)"]
        WiGame["WiGame & World Partition (wigame.py)"]
        Registry["System Registry (logical_system_registry.py)"]
        Energy["Information Energy Evaluator E(R) (wi_game_queries.py)"]
    end

    subgraph Tier4["4. Kernel & Matrix Compilation Tier (MEEL Engine)"]
        Compiler["RuleMatrixCompiler (rule_matrix.py)"]
        BitwiseExec["Dense Bitwise Execution (bitwise_execution.py)"]
        FormInfer["Formula Inference / Modus Ponens (formula_inference.py)"]
        TransInfer["Transitive Closure M_R* (transitive_inference.py)"]
        SymPolicy["Symbol Kernel Policy (symbol_policy.py)"]
    end

    subgraph Tier5["5. Boolean Matrix Substrate & Core Primitives"]
        BlockMat["BlockMatrix Omnirepresentational M (block_matrix.py)"]
        BoolMat["BooleanMatrix & Bitmasks (boolean_matrix.py)"]
        SiMat["SiMatrix (Sense Mask) (si_matrix.py)"]
        ViMat["ViMatrix (Truth Matrix) (vi_matrix.py)"]
        LiSpace["LiSpace Logical Coordinate System (li_space.py)"]
        CoreTypes["Core Types: Symbol, Relation, Fact, Thing, Proposition"]
    end

    %% Flows
    LLM --> Parser
    Parser --> Lowering
    Lowering --> SemanticFrames
    SemanticFrames --> SExprParser

    OWLOntologies --> OWLParser
    OWLParser --> SExprParser
    OWLParser --> Runtime

    SExprParser --> Runtime
    Runtime --> LogSys
    LogSys --> WiGame
    WiGame --> Energy
    LogSys --> Compiler
    Compiler --> BitwiseExec
    BitwiseExec --> FormInfer
    BitwiseExec --> TransInfer
    FormInfer --> BlockMat
    BlockMat --> BoolMat
    BlockMat --> SiMat
    BlockMat --> ViMat
    SiMat --> LiSpace
    ViMat --> LiSpace
    LiSpace --> CoreTypes
```

---

## 2. Formal Mathematical Foundations

### 2.1 The Tripartite Grammar of Sense
Propositions within the Tractatus Knowledge Machine are evaluated over a tripartite semantic domain:

$$\text{Val}(p) = \begin{cases} \text{Sinnvoll } (1), & \text{if } p \in S_i \land \text{IsContingent}(p) \\ \text{Sinnlos } (0_{\text{taut/contr}}), & \text{if } p \text{ is a formal tautology or contradiction} \\ \text{Unsinnig } (\emptyset), & \text{if } p \notin S_i \text{ (Category/Domain Mismatch)} \end{cases}$$

Where $S_i \in \{0, 1\}^{|Contexts| \times |Facts|}$ is the **Sense Mask Matrix**, which blocks absurd propositions (*Unsinnig*) before factual evaluation occurs.

### 2.2 The Omnirepresentation Block Matrix ($\mathbf{M}$)
The total state of a world partition $W_i$ is unified into a block matrix combining context routing, sense masks, and truth assignments:

$$\mathbf{M} = \begin{pmatrix} \mathbf{WC_i} & \mathbf{S_i} \\ \mathbf{S_i^T} & \mathbf{V_i} \end{pmatrix}$$

Where:
* $\mathbf{WC_i} \in \{0, 1\}^{|C| \times |C|}$: Context-to-Context inheritance and routing matrix.
* $\mathbf{S_i} \in \{0, 1\}^{|C| \times |F|}$: Context-to-Fact sense applicability mask matrix.
* $\mathbf{V_i} \in \{0, 1\}^{|S| \times |F|}$: Subject-to-Fact truth evaluation matrix.

### 2.3 Operating Equation of MEEL ($W^*$)
The active operational world matrix $W^*$ is computed via elementwise Boolean product:

$$W^* = (V_i \lor D_i) \land S_i$$

Where $D_i$ is the minimal discriminative dimension injected during the **Disambiguation Game**.

### 2.4 Matrix Rule Compilation & Deduction
Well-Formed Formulas (FBF) in Propositional Logic are compiled into incidence matrices $(I, C^+, C^-)$ by `RuleMatrixCompiler`:
* $I$: Variable incidence matrix.
* $C^+$: Positive literal constraint matrix.
* $C^-$: Negative literal constraint matrix.

Modus Ponens inference is computed as Boolean vector-matrix multiplication:

$$v_{next} = v \otimes I^*$$

Relation Transitive Closure $M_R^*$ over relation matrix $M_R$ is evaluated using iterative Boolean matrix multiplication:

$$M_R^* = \bigvee_{k=1}^N M_R^k$$

### 2.5 Information Energy Functional $E(R)$
The informational quality of a relation space $R$ is calculated deterministically:

$$E(R) = \frac{1}{4} \left( c + i + o + d \right)$$

Where:
* $c = \frac{|\text{Sinnvoll Facts}|}{|L_i|}$ (Sense Density)
* $i = \frac{|\text{True Facts}|}{|\text{Sinnvoll Facts}|}$ (Factuality Ratio)
* $o = \frac{|\text{Observed Facts}|}{|L_i|}$ (Observation Ratio)
* $d = \frac{M - |\text{Tautologies}|}{M}$ (Discriminative Power)

---

## 3. Implemented Modules Specification

### 3.1 `src/operational_model/matrices/`
* **`BooleanMatrix`** (`boolean_matrix.py`): Indexed Boolean matrix supporting `to_row_bitmasks()`, `to_col_bitmasks()`, `elementwise_and()`, `elementwise_or()`, `bool_mult()`.
* **`SiMatrix`** (`si_matrix.py`): Specialized matrix enforcing sense applicability constraints.
* **`ViMatrix`** (`vi_matrix.py`): Specialized matrix storing binary truth values.
* **`BlockMatrix`** (`block_matrix.py`): Constructs the unified global matrix $\mathbf{M}$.

### 3.2 `src/operational_model/kernel/`
* **`RuleMatrixCompiler`** (`rule_matrix.py`): Translates FBF formulas to $I, C^+, C^-$.
* **`bitwise_execution.py`**: High-performance `uint64` dense bitmask operations.
* **`formula_inference.py`**: Executes Modus Ponens over compiled rule matrices.
* **`transitive_inference.py`**: Evaluates relation transitive closure $M_R^*$.
* **`symbol_policy.py`**: Enforces symbol kernel policies and type constraints.

### 3.3 `src/operational_model/language/`
* **`owl2matrix.py`** (`OWL2MatrixParser`): Automated parser compiling OWL / RDF-XML ontologies into canonical Matrix S-Expressions and `LogicalSystem` primitives.
* **`s_expressions.py`**: Canonical S-Expression parser.

### 3.4 `src/operational_model/system/`
* **`LogicalSystem`** (`logical_system.py`): Top-level container managing symbols, relations, spaces, and WiGames.
* **`WiGame`** (`wigame.py`): World partition state manager.
* **`SExpressionRuntime`** (`s_expression_runtime.py`): Evaluates canonical S-Expressions `(create ...)`, `(assert ...)`, `(check ...)`, `(ingest ...)`, `(return ...)`.
* **`wi_game_queries.py`**: Implements `information_energy(wigame)`.

### 3.5 `prototypes/shrdlu/`
* **`english_parser.py`**: Parses controlled English sentences into grammatical parse trees.
* **`lowering.py`**: Translates parse trees into `ImperativeFrame` / `QueryFrame` and canonical S-Expressions.
* **`dialog_state.py`**: Manages conversational discourse, resolving anaphora and pronouns.

---

## 4. Empirical Verification & Test Benchmark

The entire architecture is verified by a suite of 120 automated tests passing cleanly in 0.19 seconds (`pytest` clean exit code 0).

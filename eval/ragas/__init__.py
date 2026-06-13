"""eval.ragas — RAGAS evaluation harness with NVIDIA NIM as judge (Phase 4b).

Public API
----------
    run_ragas_eval(...)  ->  RagasReport   (eval.ragas.runner)
    RagasReport          (eval.ragas.models)
    QuestionScore        (eval.ragas.models)
    MetricThresholds     (eval.ragas.models)

Optional dependency
-------------------
This sub-package requires the ``[eval-live]`` optional extra::

    pip install 'finrag[eval-live]'

The ragas package is imported lazily (inside function bodies) so importing
``eval.ragas`` itself in CI — where only ``[dev]`` is installed — is safe.
"""

from __future__ import annotations

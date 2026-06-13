"""eval.golden — golden QA dataset and schema/loader tests.

Contains:
  golden_qa.jsonl     — 10 QA pairs sourced from the NVIDIA FY2024 10-K
  test_dataset.py     — CI-safe tests: validates every row, asserts dataset
                        structure (sensitivity mix, no duplicate ids, role
                        consistency with policy)
"""

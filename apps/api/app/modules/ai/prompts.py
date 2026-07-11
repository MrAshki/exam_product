from decimal import Decimal


def build_suggest_essay_rubric_prompt(
    question_text: str,
    expected_answer: str,
    total_points: Decimal,
) -> str:
    return f"""
You are helping a teacher draft a grading rubric for an essay question.

Return JSON only.
Do not return markdown.
Do not return prose.
Do not include explanations.

Strict output structure:
{{
  "criteria": [
    {{
      "name": "...",
      "description": "...",
      "points": 0
    }}
  ],
  "total_points": 0
}}

The sum of all criteria points must equal {total_points}.

Question:
{question_text}

Expected answer:
{expected_answer}
""".strip()

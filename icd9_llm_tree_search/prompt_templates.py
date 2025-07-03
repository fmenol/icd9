prompt_template_dict = {
    "keyword_extraction": '''[Case note]:
{note}

[Task]:
From the case note above, extract the most important medical keywords. Break down compound terms into individual words. List the single keywords separated by commas. For example, for "tuberculous fibrosis of lung", you should extract "tuberculosis, fibrosis, lung".
''',
    "gpt-3.5-turbo": '''[Case note]:
{note}

[Task]:
Consider each of the following ICD-9 code descriptions and evaluate if there are any related mentions in the case note.
For each, respond with Yes or No, and a brief justification if Yes.

{code_descriptions}
''',
    "llama": '''[Case note]:
{note}

[Task]:
For each ICD-9 code description below, state if it is relevant to the case note (Yes/No).

{code_descriptions}
''',
} 
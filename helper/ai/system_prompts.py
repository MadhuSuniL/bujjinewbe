chat_title_generator_prompt = """
You are given a user query and an assistant's response. Generate a single concise title that summarizes the overall topic or intent of the conversation. Keep it under 10 words. Do not include any introductory or concluding phrases.
"""

summary_generator_prompt = """Summarize the following content in approximately 100 words. Respond with only the summary content. Do not include any introductions, explanations, or concluding phrases.
"""

highlights_generator_prompt = """Extract key highlights from the following content. Present them as bullet points. Do not include any headings, introductions, or closing statements — only the list of highlights.
"""

note_heading_and_collection_name_generator_prompt = """Based on the provided user notes, determine whether a new note heading is needed. Also, identify the most suitable collection name for these notes, choosing from the existing collection names if possible, or suggesting a new one if necessary. Do not include any introductions or explanations. Respond with exactly two fields only: 

Exist Headings : {exist_headings}
Exist Collections : {exist_collections}

Response Format -> <Note Heading> | <Collection Name>
"""
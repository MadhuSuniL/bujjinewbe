from __future__ import annotations
import re
import spacy
import wikipedia
from typing import List
from dotenv import load_dotenv
from helper.ai.splitter import Splitter
from helper.ai.vector_dbs import ChromaVectorDB
from chats_app.models import VectorStoreWikipediaFlag
from langchain_community.tools import WikipediaQueryRun
from langchain_cohere.embeddings import CohereEmbeddings
from langchain_core.messages import BaseMessage, SystemMessage

load_dotenv()

class WikipediaQueryRunWithVectorDBStore(WikipediaQueryRun):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object.__setattr__(self, 'store', ChromaVectorDB(embeddings=CohereEmbeddings(model="embed-english-v3.0")).store)
        

    def get_page_title_from_the_response(self, response: str):
        page_line = response.split('\n')[0]
        title_pattern = r"Page: (.+)"
        match = re.match(title_pattern, page_line)
        if match:
            return match.group(1)
        return None

    def get_page(self, page_title: str):
        return wikipedia.WikipediaPage(page_title)

    def get_images_from_page(self, page: wikipedia.WikipediaPage):
        return [image for image in page.images if not image.endswith('.svg')]

    def get_url_from_page(self, page: wikipedia.WikipediaPage):
        return page.url

    def get_content_from_page(self, page: wikipedia.WikipediaPage):
        return page.content

    def get_references_from_page(self, page: wikipedia.WikipediaPage):
        return page.references[:20]

    def get_summary_from_page(self, page: wikipedia.WikipediaPage):
        return page.summary

    def save_images_to_vector_db(self, page_title: str, images: list):
        image_lines = "\n".join([f"{index + 1}. {image}" for index, image in enumerate(images)])
        content = f"{page_title} Images Links\n\n{image_lines}"
        documents = Splitter.get_document(content)
        if self.vector_save_flag:
            self.store.add_documents(documents)
        return content

    def save_url_to_vector_db(self, page_title: str, url: str):
        content = f"{page_title} Url\n{url}"
        documents = Splitter.get_document(content)
        if self.vector_save_flag:
            self.store.add_documents(documents)
        return content

    def save_content_to_vector_db(self, content: str):
        documents = Splitter.split_and_get_documents(content)
        if self.vector_save_flag:
            self.store.add_documents(documents)
        return content

    def save_references_to_vector_db(self, page_title: str, references: list):
        references_text = "\n".join([f"{index + 1}. {reference}" for index, reference in enumerate(references)])
        content = f"{page_title} References Links\n\n{references_text}"
        documents = Splitter.get_document(content)
        if self.vector_save_flag:
            self.store.add_documents(documents)
        return content

    def save_summary_to_vector_db(self, page_title: str, summary: str):
        content = f"{page_title} Summary\n{summary}"
        documents = Splitter.get_document(content)
        if self.vector_save_flag:
            self.store.add_documents(documents)
        return content

    def save_the_resources_to_vector_db(self, response: str):
        page_title = self.get_page_title_from_the_response(response)
        if not page_title:
            return response, "", "", "", ""

        page = self.get_page(page_title)
        images = self.get_images_from_page(page)
        url = self.get_url_from_page(page)
        content = self.get_content_from_page(page)
        references = self.get_references_from_page(page)
        summary = self.get_summary_from_page(page)

        flag_obj, vector_save_flag = VectorStoreWikipediaFlag.flag(page_title=page_title)
        object.__setattr__(self, 'flag_obj', flag_obj)
        object.__setattr__(self, 'vector_save_flag', vector_save_flag)
        

        content = self.save_content_to_vector_db(content)
        images = self.save_images_to_vector_db(page_title, images)
        references = self.save_references_to_vector_db(page_title, references)
        url = self.save_url_to_vector_db(page_title, url)
        summary = self.save_summary_to_vector_db(page_title, summary)

        if self.vector_save_flag:
            self.flag_obj.done()

        return page_title, images, url, references, summary


    def invoke(self, *args, **kwargs):
        response = super().invoke(*args, **kwargs)
        page_title, images, url, references, summary = self.save_the_resources_to_vector_db(response)
        response = f"""
        {page_title}\n\n
        {url}\n\n
        {summary}\n\n
        {images}\n\n
        {references}\n\n
        """
        return response


class TrimMessages:
    """Class to trim messages based on token limits, optimized for latency and memory."""
    
    def __init__(self):
        # Initialize the spaCy tokenizer once during object creation.
        nlp = spacy.load("en_core_web_md")
        self.tokenizer = nlp.tokenizer

    def invoke(self, messages: List[BaseMessage], token_limit: int = 6000) -> List[BaseMessage]:
        """
        Trim a list of message objects to ensure their combined tokens do not exceed the token limit.
        If a message exceeds the remaining tokens, modify its content in-place to include only the
        tokens that fit within the limit, handling punctuation to avoid unnecessary spaces.
        """
        total_tokens = 0
        system_message, *remaining_messages = messages
        trimmed_messages = [system_message]
        
        for message in reversed(messages):
            # Use only the tokenizer to avoid overhead of full NLP pipeline.
            if isinstance(message, SystemMessage):
                trimmed_messages.append(message)
                continue
            # Tokenize the message content.
            doc = self.tokenizer(message.content)
            num_tokens = len(doc)
            
            # If the entire message fits within the limit, use it as is.
            if total_tokens + num_tokens <= token_limit:
                trimmed_messages.insert(0, message)
                total_tokens += num_tokens
            else:
                # Determine how many tokens we can still add.
                remaining_tokens = token_limit - total_tokens
                if remaining_tokens > 0:
                    tokens = doc[:remaining_tokens]
                    # Build the trimmed content token by token.
                    trimmed_content = tokens[0].text
                    for token in tokens[1:]:
                        # Avoid inserting an extra space before punctuation.
                        if token.is_punct:
                            trimmed_content += token.text
                        else:
                            trimmed_content += " " + token.text
                    # Modify the message object in place.
                    message.content = trimmed_content
                    trimmed_messages.append(message)
                    total_tokens += remaining_tokens
                break  # Stop processing further messages as the token limit is reached.
        
        return trimmed_messages


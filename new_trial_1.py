# -*- coding: utf-8 -*-
"""
Created on Wed May 21 06:38:26 2025

@author: Admin
"""

import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, Document
from typing import List, Optional
from llama_index.core.bridge.pydantic import Field

pattern1 = r"^((\d+\.)+\s*.*)$"
# pattern2 

class SectionNodeParser(NodeParser):
    """
    A custom NodeParser that splits a document into sections based on defined heading patterns.
    """
    section_heading_pattern: str = Field(
        default=r"^((\d+\.)+\s*.*)$", # Matches "1. Glossary", "1.1. Adverse Drug Reaction (ADR)", "1.1.2. Sub-section"
        description="Regular expression pattern to identify section headings."
    )
    include_text_in_metadata: bool = Field(
        default=True,
        description="Whether to include the full section text in metadata (for debugging)."
    )

    def __init__(
        self,
        section_heading_pattern: Optional[str] = None,
        include_text_in_metadata: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        if section_heading_pattern is not None:
            self.section_heading_pattern = section_heading_pattern
        self._compiled_section_heading_pattern = re.compile(self.section_heading_pattern, re.MULTILINE)
        
        self.include_text_in_metadata = include_text_in_metadata


    def _parse_nodes(self, documents: List[Document], show_progress: bool = False) -> List[TextNode]:
        """
        Splits documents into sections based on heading patterns.
        Assumes each document is a full text document for simplicity in this example.
        """
        all_nodes: List[TextNode] = []
        for doc in documents:
            text = doc.text
            matches = list(self._compiled_section_heading_pattern.finditer(text))

            if not matches:
                # If no sections found, treat the whole document as one node
                all_nodes.append(TextNode(
                    text=text,
                    metadata={"section": "Full Document", "page_label": doc.metadata.get("page_label", "N/A")}
                ))
                continue

            current_section_start_idx = 0
            current_section_title = "Document Preamble" 

            for i, match in enumerate(matches):
                # Content from previous section end to current section start
                content_chunk = text[current_section_start_idx:match.start()].strip()

                if content_chunk:
                    node_text = content_chunk
                    metadata = {
                        "section": current_section_title,
                        "page_label": doc.metadata.get("page_label", "N/A")
                    }
                    if self.include_text_in_metadata:
                        metadata["full_section_content"] = node_text
                    all_nodes.append(TextNode(text=node_text, metadata=metadata))

                # Update for the next section: The title of the current match
                current_section_title = match.group(0).strip()
                current_section_start_idx = match.end()

            # Add the last section
            last_section_content = text[current_section_start_idx:].strip()
            if last_section_content:
                node_text = last_section_content
                metadata = {
                    "section": current_section_title,
                    "page_label": doc.metadata.get("page_label", "N/A")
                }
                if self.include_text_in_metadata:
                    metadata["full_section_content"] = node_text
                all_nodes.append(TextNode(text=node_text, metadata=metadata))

        return all_nodes

# --- How to Use It ---

# 2. Load the PDF document
reader = SimpleDirectoryReader(input_files=["ich-gcp-r2-step-5.pdf"])
documents = reader.load_data()

# 3. Initialize your custom SectionNodeParser
section_parser = SectionNodeParser(
    # section_heading_pattern=r"^((\d+\.)+\s*.*)$"
)

# 4. Parse the nodes using your custom parser
nodes = section_parser.get_nodes_from_documents(documents)

# --- Print nodes to console as requested ---
print("--- Extracted Sections ---")
for i, node in enumerate(nodes):
    # print(f"\n--- Node {i+1} Section: {node.metadata.get('section', 'N/A')} (Page: {node.metadata.get('page_label', 'N/A')}) ---")
    print(f"--- Node {i+1} Section: {node.metadata.get('section')} ---")
    # print(f"Content (first 200 chars): {node.text[:200]}...")
    # print(f"Full content length: {len(node.text)} characters.")
    # print("-" * 40)

nodes_as_dicts = [node.dict() for node in nodes]

# save the nodes to a JSON file
import json
out_file_name = "parsed_nodes_ich_gcp_new_trial_1.json"

with open(out_file_name, "w", encoding="utf-8") as f:
    json.dump(nodes_as_dicts, f, indent=2, ensure_ascii=False)
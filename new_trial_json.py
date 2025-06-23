# -*- coding: utf-8 -*-
"""
Created on Tue May 20 21:18:33 2025

@author: Admin
"""

import re
import json
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, Document
from typing import List, Optional
from llama_index.core.bridge.pydantic import Field

class SectionNodeParser(NodeParser):
    """
    A custom NodeParser that splits a document into sections based on defined heading patterns.
    """
    section_heading_pattern: str = Field(
        default=r"^(Chapter\s+\d+:[\s\w]+|(\d+\.)+\s+[\w\s]+)$",
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
            current_section_title = "Document Start" # Default for content before first heading

            for i, match in enumerate(matches):
                # Content from previous section end to current section start
                content_before_current_heading = text[current_section_start_idx:match.start()].strip()

                if content_before_current_heading:
                    node_text = content_before_current_heading
                    metadata = {
                        "section": current_section_title,
                        "page_label": doc.metadata.get("page_label", "N/A")
                    }
                    if self.include_text_in_metadata:
                        metadata["full_section_content"] = node_text
                    all_nodes.append(TextNode(text=node_text, metadata=metadata))

                # Now process the current section heading itself as a section marker
                current_section_title = match.group(0).strip()
                current_section_start_idx = match.end() # Update start index for the next section to be AFTER the heading

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
    section_heading_pattern=r"^(Chapter\s+\d+:\s+[\w\s]+|(\d+\.)+\s+[\w\s]+)$"
)

# 4. Parse the nodes using your custom parser
nodes = section_parser.get_nodes_from_documents(documents)

# --- Convert to JSON format ---
extracted_sections_json = []
for node in nodes:
    section_data = {
        "section_title": node.metadata.get("section", "N/A"),
        "page_label": node.metadata.get("page_label", "N/A"),
        "content": node.text,
        # You can add other metadata fields if needed
        # "id": node.id_
    }
    extracted_sections_json.append(section_data)

# Pretty print the JSON to console
print(json.dumps(extracted_sections_json, indent=2))

# Optionally, save to a JSON file
output_json_filename = "extracted_sections.json"
with open(output_json_filename, "w", encoding="utf-8") as f:
    json.dump(extracted_sections_json, f, indent=2, ensure_ascii=False)

print(f"\nExtracted sections saved to {output_json_filename}")

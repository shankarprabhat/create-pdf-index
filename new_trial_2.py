import re
from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, Document
from typing import List, Optional
from llama_index.core.bridge.pydantic import Field

class SectionNodeParser(NodeParser):
    """
    A custom NodeParser that splits a document into sections based on defined heading patterns.
    """
    section_heading_pattern: str = Field(
        default=r"^((\d+\.)+\s*.*)$", # Matches "1. Glossary", "1.1. Adverse Drug Reaction (ADR)", etc.
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
        """
        all_nodes: List[TextNode] = []
        for doc in documents:
            text = doc.text
            matches = list(self._compiled_section_heading_pattern.finditer(text))

            # Handle content *before* the first heading
            if matches and matches[0].start() > 0:
                preamble_content = text[0:matches[0].start()].strip()
                if preamble_content:
                    metadata = {
                        "section": "Document Preamble",
                        "page_label": doc.metadata.get("page_label", "N/A")
                    }
                    if self.include_text_in_metadata:
                        metadata["full_section_content"] = preamble_content
                    all_nodes.append(TextNode(text=preamble_content, metadata=metadata))
            elif not matches and text.strip(): # If no headings but there's text
                 metadata = {
                        "section": "Full Document Content",
                        "page_label": doc.metadata.get("page_label", "N/A")
                    }
                 if self.include_text_in_metadata:
                    metadata["full_section_content"] = text.strip()
                 all_nodes.append(TextNode(text=text.strip(), metadata=metadata))


            for i, match in enumerate(matches):
                section_title = match.group(0).strip() # The exact matched heading line
                start_content_idx = match.end()       # Content starts right after the heading

                end_content_idx = len(text)
                if i + 1 < len(matches):
                    # The content for this section ends just before the next heading starts
                    end_content_idx = matches[i+1].start()

                section_content = text[start_content_idx:end_content_idx].strip()

                # Only create a node if there's actual content for this section
                if section_content:
                    node_text = section_content
                    metadata = {
                        "section": section_title,
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
# Using the regex that correctly identifies "1. Glossary", "1.1. Adverse...", etc.
section_parser = SectionNodeParser(
    # section_heading_pattern=r"^((\d+\.)+\s*.*)$"
)

# 4. Parse the nodes using your custom parser
nodes = section_parser.get_nodes_from_documents(documents)

# --- Print nodes to console ---
print("--- Extracted Sections ---")
for i, node in enumerate(nodes):
    print(f"--- Node {i+1} Section: {node.metadata.get('section')} ---")
    # print(f"\n--- Node {i+1} Section: {node.metadata.get('section', 'N/A')} (Page: {node.metadata.get('page_label', 'N/A')}) ---")
    # print(f"Content (first 200 chars): {node.text[:200]}...")
    # print(f"Full content length: {len(node.text)} characters.")
    # print("-" * 40)

nodes_as_dicts = [node.dict() for node in nodes]

# save the nodes to a JSON file
import json
out_file_name = "parsed_nodes_ich_gcp_new_trial_2.json"

with open(out_file_name, "w", encoding="utf-8") as f:
    json.dump(nodes_as_dicts, f, indent=2, ensure_ascii=False)
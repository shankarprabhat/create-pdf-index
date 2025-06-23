# -*- coding: utf-8 -*-
"""
Created on Wed May 21 07:37:14 2025

@author: Admin
"""

import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, Document
from typing import List, Optional, Dict
from llama_index.core.bridge.pydantic import Field
import os
import uuid # Import uuid for generating unique IDs

class SectionNodeParser(NodeParser):
    """
    A custom NodeParser that splits a document into sections based on defined heading patterns,
    and includes hierarchical information in node metadata.
    """
    section_heading_pattern: str = Field(
        # The most robust regex for your document's numeric and indented headings
        default=r"^\s*(\d+(\.\d+)*)\s{1,}([^\n]*)$", 
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

        # Ensure the correct pattern is used, either from init or the class default
        if section_heading_pattern is not None:
            self.section_heading_pattern = section_heading_pattern
        else:
            self.section_heading_pattern = self.__fields__["section_heading_pattern"].default

        self._compiled_section_heading_pattern = re.compile(self.section_heading_pattern, re.MULTILINE)
        
        self.include_text_in_metadata = include_text_in_metadata


    def _parse_nodes(self, documents: List[Document], show_progress: bool = False) -> List[TextNode]:
        """
        Splits documents into sections based on heading patterns, adding hierarchical metadata.
        """
        all_nodes: List[TextNode] = []
        for doc in documents:
            text = doc.text
            matches = list(self._compiled_section_heading_pattern.finditer(text))

            # Maintain a stack of current parent nodes at each level.
            # Key: heading_level (int), Value: (node_id_of_parent, heading_id_string_of_parent)
            current_parent_nodes: Dict[int, tuple[str, str]] = {}
            
            # Handle content *before* the first heading (Preamble)
            if matches and matches[0].start() > 0:
                preamble_content = text[0:matches[0].start()].strip()
                if preamble_content:
                    node_id = str(uuid.uuid4()) # Generate a unique ID for the preamble node
                    metadata = {
                        "section": "Document Preamble",
                        "page_label": doc.metadata.get("page_label", "N/A"),
                        "node_id": node_id, # Store its own ID
                        "heading_level": 0 # Assign level 0 for preamble
                    }
                    if self.include_text_in_metadata:
                        metadata["full_section_content"] = preamble_content
                    
                    preamble_node = TextNode(text=preamble_content, metadata=metadata, id_=node_id)
                    all_nodes.append(preamble_node)
                    # The preamble itself could be a parent for the first actual heading (level 1)
                    current_parent_nodes[0] = (node_id, "Preamble") # Store preamble as level 0 parent


            # Handle documents with no headings (treat entire document as one node)
            elif not matches and text.strip(): 
                node_id = str(uuid.uuid4())
                metadata = {
                    "section": "Full Document Content",
                    "page_label": doc.metadata.get("page_label", "N/A"),
                    "node_id": node_id,
                    "heading_level": 0
                }
                if self.include_text_in_metadata:
                    metadata["full_section_content"] = text.strip()
                all_nodes.append(TextNode(text=text.strip(), metadata=metadata, id_=node_id))
                continue


            # Process each detected heading
            for i, match in enumerate(matches):
                section_title_line = match.group(0).strip() # e.g., "   1.1     Study Aims"
                section_heading_id = "" # e.g., "1.1"
                heading_level = 0
                
                # Extract the numeric ID part (e.g., "1.1" from "   1.1     Study Aims")
                # This regex extracts the sequence of numbers and dots.
                numeric_part_match = re.search(r"(\d+(?:\.\d+)*)", section_title_line)
                if numeric_part_match:
                    section_heading_id = numeric_part_match.group(1) # Get "1.1" or "4.1.1"
                    heading_level = len(section_heading_id.split('.')) # Level 1 for "1", 2 for "1.1" etc.


                # Determine the parent_node_id based on hierarchy
                parent_node_id = None
                # Iterate through current parent nodes from highest level downwards
                for level in sorted(current_parent_nodes.keys(), reverse=True):
                    if level < heading_level: # Find the most immediate parent in the hierarchy
                        parent_node_id = current_parent_nodes[level][0] # Get the node_id of that parent
                        break # Found the direct parent, stop searching


                # Remove any parent entries that are at the same or lower level than the current heading.
                # This "pops" items off the hierarchy stack as we move to a sibling or higher-level parent.
                levels_to_remove = [level for level in current_parent_nodes if level >= heading_level]
                for level in levels_to_remove:
                    del current_parent_nodes[level]

                
                # Extract the content associated with this section
                start_content_idx = match.end()       
                end_content_idx = len(text)
                if i + 1 < len(matches): # Content ends before the next heading (if any)
                    end_content_idx = matches[i+1].start()
                section_content = text[start_content_idx:end_content_idx].strip()

                if section_content:
                    node_id = str(uuid.uuid4()) # Generate a unique ID for this section's node
                    node_text = section_content # The actual text content of the section
                    
                    metadata = {
                        "section": section_title_line, # Store the full heading line for display
                        "heading_id": section_heading_id, # e.g., "1.1", "4.1.1"
                        "heading_level": heading_level, # e.g., 1, 2, 3
                        "page_label": doc.metadata.get("page_label", "N/A"),
                        "node_id": node_id # Store its own unique ID
                    }
                    if parent_node_id:
                        metadata["parent_node_id"] = parent_node_id # Link to its parent node's ID
                    
                    if self.include_text_in_metadata:
                        metadata["full_section_content"] = node_text # Optional: full content in metadata

                    # Create the TextNode with the collected metadata and unique ID
                    node = TextNode(text=node_text, metadata=metadata, id_=node_id)
                    all_nodes.append(node)
                    
                    # Add this node to the current_parent_nodes stack for its level
                    # It becomes a potential parent for subsequent lower-level headings
                    current_parent_nodes[heading_level] = (node_id, section_heading_id)

        return all_nodes

# --- Your Usage Code (example) ---

# 1. (Optional) Create a dummy PDF content for demonstration
dummy_pdf_content = """
Guideline for good clinical practice E6(R2)
EMA/CHMP/ICH/135/1995 Page 7/68

This is some introductory text before the first formal section.

1.  Glossary
    1.1     Adverse Drug Reaction (ADR)
In the pre-approval clinical experience with a new medicinal product or its new usages, particularly as
the therapeutic dose(s) may not be established: all noxious and unintended responses to a medicinal
product related to any dose should be considered adverse drug reactions. The phrase responses to a
medicinal product means that a causal relationship between a medicinal product and an adverse event
is at least a reasonable possibility, i.e. the relationship cannot be ruled out.
Regarding marketed medicinal products: a response to a drug which is noxious and unintended and
which occurs at doses normally used in man for prophylaxis, diagnosis, or therapy of diseases or for
modification of physiological function (see the ICH Guideline for Clinical Safety Data Management:
Definitions and Standards for Expedited Reporting).
    1.2. Adverse Event (AE)
Any untoward medical occurrence in a patient or clinical investigation subject administered a
pharmaceutical product and which does not necessarily have a causal relationship with this treatment.
An adverse event (AE) can therefore be any unfavourable and unintended sign (including an abnormal
laboratory finding), symptom, or disease temporally associated with the use of a medicinal
(investigational) product, whether or not related to the medicinal (investigational) product (see the
ICH Guideline for Clinical Safety Data Management: Definitions and Standards for Expedited
Reporting).
1.3. Amendment (to the protocol)
See Protocol Amendment.
    4. Research Plan
    4.1     Study Aims
    Primary Aim: Investigate
    4.1.1   Sub-Aim 1: First detailed point
    4.1.2   Sub-Aim 2: Second detailed point
    4.2     Methods
    This section discusses the methods used in the study.
1.4. Applicable regulatory requirement(s)
Any law(s) and regulation(s) addressing the conduct of clinical trials of investigational products.
"""

# IMPORTANT: Choose ONE of the following options:
# Option A: Use a real PDF file
# reader = SimpleDirectoryReader(input_files=["your_document.pdf"])

# Option B: Use the dummy content for testing
processed_content = "\n".join([line.strip() for line in dummy_pdf_content.strip().splitlines() if line.strip()])
dummy_file_path = "temp_dummy_document.pdf"
with open(dummy_file_path, "w", encoding="utf-8") as f:
    f.write(processed_content)
reader = SimpleDirectoryReader(input_files=["ich-gcp-r2-step-5.pdf"])

documents = reader.load_data()

# 3. Initialize your custom SectionNodeParser
section_parser = SectionNodeParser(
    # The pattern is now handled by the Field default, but you can explicitly pass it here too:
    section_heading_pattern=r"^\s*(\d+(\.\d+)*)\s{1,}([^\n]*)$" 
)

# 4. Parse the nodes using your custom parser
nodes = section_parser.get_nodes_from_documents(documents)

# --- Print nodes to console to inspect hierarchical metadata ---
print("--- Extracted Sections with Hierarchy ---")
for i, node in enumerate(nodes):
    print(f"--- Node {i+1} ---")
    print(f"  Section Title: {node.metadata.get('section')}")
    print(f"  Heading ID: {node.metadata.get('heading_id')}")
    print(f"  Heading Level: {node.metadata.get('heading_level')}")
    print(f"  Node ID: {node.metadata.get('node_id')}")
    print(f"  Parent Node ID: {node.metadata.get('parent_node_id')}")
    print(f"  Content (first 100 chars): {node.text[:100]}...")
    print("-" * 50)
    
nodes_as_dicts = [node.dict() for node in nodes]

# Clean up the dummy file
# if 'dummy_file_path' in locals() and os.path.exists(dummy_file_path):
#     os.remove(dummy_file_path)
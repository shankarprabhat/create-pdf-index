import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode, Document
from typing import List, Optional
from llama_index.core.bridge.pydantic import Field # Import Field

class SectionNodeParser(NodeParser):
    """
    A custom NodeParser that splits a document into sections based on defined heading patterns.
    """
    section_heading_pattern: str = Field(
        # default=r"^(Chapter\s+\d+:[\s\w]+|(\d+\.)+\s+[\w\s]+|((\d+\.)+\s*.*))$",
        # default=r"^(Chapter\s+\d+:[\s\w]+|(\d+\.)+\s*.*)$",
        # default=r"^(Chapter\s+\d+:[\s\w]+|(\d+\.)+\s*.*)|((\d+\.)+\s*[^\n]*)$",
        # default=r"^((\d+\.)+\s*[\w\s\(\)\-]*)$",
        # default=r"^\s*((\d+\.)+\s*[\w\s\(\)\-]*)$",
        # default=r"^.*?((\d+\.)+\s*[\w\s\(\)\-]*)$",
        default=r"^\s*(\d+(\.\s*)?)+\s*[^\n]*$",
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
        super().__init__(**kwargs) # Call parent __init__ first

        # Initialize the fields after super().__init__
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
                        metadata["full_section_content"] = node_text # Store content as well
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
# reader = SimpleDirectoryReader(input_files=["NITLT01.pdf"])  #AZD9291
# reader = SimpleDirectoryReader(input_files=["AZD9291.pdf"])  #AZD9291
documents = reader.load_data()

# 3. Initialize your custom SectionNodeParser
# NOTE: The regex needs to be precise for your document structure.
# I've updated the default to better match the dummy content.
section_parser = SectionNodeParser(
    section_heading_pattern=r"^\s*(\d+(\.\s*)?)+\s*[^\n]*$"    #r"^(Chapter\s+\d+:\s+[\w\s]+|(\d+\.)+\s+[\w\s]+)$"
)

# 4. Parse the nodes using your custom parser
# The get_nodes_from_documents method is the public interface you should call
nodes = section_parser.get_nodes_from_documents(documents) 

print(f"Total nodes created: {len(nodes)}\n")

for i, node in enumerate(nodes):
    pass
    print(f"--- Node {i+1} Section: {node.metadata.get('section')} ---")
    # print(f"Section: {node.metadata.get('section')}")
    # print(f"Content (first 200 chars): {node.text[:200]}...")
    # print(f"Content length: {len(node.text)}")
    # print("-" * 20)

nodes_as_dicts = [node.dict() for node in nodes]

# 5. (Optional) Build an index and query
# If you build an index, you can then query specific sections.
# from llama_index.embeddings.openai import OpenAIEmbedding # Example embedding model
# from llama_index.llms.openai import OpenAI # Example LLM

# # Ensure you have an LLM and Embedding model configured if you want to run this part
# # Settings.llm = OpenAI(model="gpt-3.5-turbo")
# # Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002")

# # index = VectorStoreIndex(nodes)
# # query_engine = index.as_query_engine()
# # response = query_engine.query("What is the problem statement?")
# # print(f"\nQuery Response: {response}")

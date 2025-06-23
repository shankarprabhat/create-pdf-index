import re
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import NodeParser
from llama_index.core.schema import TextNode

# Assume you have a custom SectionNodeParser defined
class SectionNodeParser(NodeParser):
    def get_nodes_from_documents(self, documents):
        nodes = []
        for doc in documents:
            # Logic to identify sections and create TextNodes with metadata
            # This is the core custom part
            lines = doc.text.splitlines()
            current_section = None
            section_content = ""
            for line in lines:
                if is_section_heading(line): # Your function to identify headings
                    if current_section:
                        nodes.append(TextNode(text=section_content.strip(), metadata={"section": current_section}))
                    current_section = line.strip()
                    section_content = ""
                else:
                    section_content += line + "\n"
            if current_section:
                nodes.append(TextNode(text=section_content.strip(), metadata={"section": current_section}))
        return nodes

def is_section_heading(line):
    # Implement your logic to identify section headings
    # e.g., check for lines starting with "Chapter", numbers, bold text indicators (if possible)
    return line.startswith("Chapter") or re.match(r"^\d+(\.\d+)*\s", line)

# Load the PDF
reader = SimpleDirectoryReader(input_files=["ich-gcp-r2-step-5.pdf"])
documents = reader.load_data()

# Initialize the custom node parser
# section_parser = SectionNodeParser()
section_parser = SectionNodeParser(section_heading_pattern=r"^(Chapter\s+\d+:\s+[\w\s]+|(\d+\.)+\s+[\w\s]+)$")
nodes = section_parser.get_nodes_from_documents(documents)
print(nodes)

# Build the index
# index = VectorStoreIndex(nodes)

# # Now you can query based on sections
# query_engine = index.as_query_engine()
# response = query_engine.query("What are the key findings in Chapter 3?")
# print(response)
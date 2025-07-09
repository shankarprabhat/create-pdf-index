# This file reads a pdf document with Llama parse library, and stores the data in local
from llama_parse import LlamaParse
import time
import json
import os
import dotenv
import re

# Define your desired JSON schema. This tells LlamaParse what structure you expect.
# For sections and subsections, you'd typically want a recursive structure.
# This is a simplified example; you might need to make it more complex based on your PDF's structure.
dotenv.load_dotenv()
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

file_name = "source/ich-gcp-r2-step-5.pdf"
file_name = "source/21 CFR Part 50_test.pdf"
file_name = "source/21 CFR Part 50.pdf"
extra_info = {"file_name": file_name}

base_name = os.path.basename(file_name)
extracted_name = os.path.splitext(base_name)[0]

def read_as_markdown(file_name):
    
    parser = LlamaParse(
       api_key=LLAMA_CLOUD_API_KEY,  # if you did not create an environmental variable you can set the API key here
       result_type="markdown",  # "markdown" and "text" are available
       page_separator="---PAGE_BREAK__{pageNumber}---",
       system_prompt_append=("Prioritize '§ X.X' as the highest level heading (level 1). Lines starting with '(a)', '(b)', '(c)' should always be treated as nested subsections under the nearest '§ X.X' section, and should not be standalone headings. Lines starting with '(1)', '(2)', '(3)' should always be treated as sub-subsections under the nearest '(a)/(b)/...' subsection."),
       verbose = True
       )
    with open(f"./{file_name}", "rb") as f:
       # must provide extra_info with file_name key with passing file object
       documents = parser.load_data(f, extra_info=extra_info)

    # Write the output to a file
    fname = extracted_name+".md"
    with open(fname, "w", encoding="utf-8") as f:
       for doc in documents:
           f.write(doc.text)
           
def pre_process_llamaparse_markdown(markdown_text):
    lines = markdown_text.split('\n')
    processed_lines = []

    for line in lines:
        # Check for lines that LlamaParse might have incorrectly made into '##' (H2)
        # but should be just '(a)' or '(b)' etc.
        match_h2_lettered = re.match(r'^##\s*\(([a-z])\)\s*(.*)', line)
        if match_h2_lettered:
            # Revert to just the (a) format, removing the '##'
            processed_lines.append(f"({match_h2_lettered.group(1)}) {match_h2_lettered.group(2)}")
            continue

        # Check for lines that LlamaParse might have incorrectly made into '###' (H3)
        # but should be just '(1)' or '(2)' etc.
        match_h3_numbered = re.match(r'^###\s*\(([0-9])\)\s*(.*)', line)
        if match_h3_numbered:
            # Revert to just the (1) format, removing the '###'
            processed_lines.append(f"({match_h3_numbered.group(1)}) {match_h3_numbered.group(2)}")
            continue

        # You might also need to adjust if it makes '§ X.X' into '##' instead of '#':
        match_h2_section = re.match(r'^##\s*(§\s*\d+\.\d+)\s*(.*)', line)
        if match_h2_section:
            # Change '##' to '#' for main sections if they are identified as H2
            processed_lines.append(f"# {match_h2_section.group(1)} {match_h2_section.group(2)}")
            continue

        # Add other specific clean-up rules as you observe patterns in LlamaParse's output
        # For example, if it adds extra blank lines or odd characters.

        processed_lines.append(line)
        
    # Save the raw LlamaParse output (or your initial markdown content)
    with open("chk.md", 'w', encoding='utf-8') as f:
        f.write("\n".join(processed_lines))
    # print(f"Raw LlamaParse (or initial) markdown saved to '{intermediate_markdown_file_path}'")

    return "\n".join(processed_lines)

# --- How to integrate this ---
# 1. Get markdown_content from LlamaParse
# markdown_content = llamaparse_response_data

# 2. Pre-process the markdown
# cleaned_markdown_content = pre_process_llamaparse_markdown(markdown_content)

# 3. Then pass to your fixed parser
# extracted_sections_json = parse_regulatory_markdown_to_sections_fixed(cleaned_markdown_content)

def read_pdf_as_json(file_name):   
    json_schema_dict_simple = {
        "type": "object",
        "properties": {
            "document_title": {"type": "string"},
            "parts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "heading": {"type": "string"},
                        "text_content": {"type": "string"}
                    },
                    "required": ["heading", "text_content"]
                }
            }
        },
        "required": ["document_title", "parts"]
    }
    json_schema_string_simple = json.dumps(json_schema_dict_simple)
    # Pass this simple string to LlamaParse

    json_schema_dict = {
        "type": "object",
        "properties": {
            "document_title": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "subsections": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string"},
                                    "content": {"type": "string"},
                                    # You can nest further if needed
                                },
                                "required": ["title", "content"]
                            }
                        }
                    },
                    "required": ["title", "content"]
                }
            }
        },
        "required": ["document_title", "sections"]
    }

    # Convert the Python dictionary schema to a JSON string
    json_schema_string = json.dumps(json_schema_dict)
        
    parser = LlamaParse(
        # api_key=os.environ.get("LLAMA_CLOUD_API_KEY"),
        api_key=LLAMA_CLOUD_API_KEY,  # if you did not create an environmental variable you can set the API key here
        result_type="json", # Request JSON output
        structured_output_json_schema=json_schema_string_simple, # Provide your schema
        # Add any other parsing options here, e.g., for tables, etc.
        verbose=True
    )
    
    tic = time.time()
    
    try:
        with open(f"./{file_name}", "rb") as f:
            # Load data with the parser. It will attempt to match the schema.
            documents = parser.load_data(f, extra_info=extra_info)
    
        # LlamaParse returns a list of Document objects.
        # When `result_type="json"` and `structured_output_json_schema` is used,
        # the `doc.text` will contain the JSON string.
    
        parsed_json_data = []
        for doc in documents:
            try:
                # The 'text' attribute of the document will contain the JSON string
                json_content = json.loads(doc.text)
                parsed_json_data.append(json_content)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from LlamaParse output: {e}")
                print(f"Problematic text: {doc.text[:500]}...") # Print first 500 chars for debugging
                # If parsing fails for a doc, you might want to log it or handle it.
    
        # Write the extracted JSON to a file
        output_json_file = extracted_name + ".json"
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(parsed_json_data, f, indent=4, ensure_ascii=False)
    
        print(f"Extracted content and sections saved to '{output_json_file}'")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure your LLAMA_CLOUD_API_KEY is correctly set.")
    
    toc = time.time()
    print(f"time: {toc-tic}")   


def parse_markdown_to_sections(markdown_text):
    """
    Parses markdown text into a hierarchical dictionary based on headings.
    It assumes standard Markdown headings (#, ##, ###, etc.) and
    associates content with the heading that precedes it.
    """
    sections_data = []
    current_section = None
    current_subsection = None
    current_sub_subsection = None # For up to H3, can extend further

    lines = markdown_text.split('\n')
    for line in lines:
        # Regex for different heading levels
        h1_match = re.match(r'^#\s*(.*)', line)
        h2_match = re.match(r'^##\s*(.*)', line)
        h3_match = re.match(r'^###\s*(.*)', line)
        # Add more heading levels (H4, H5, H6) if your document uses them

        if h1_match:
            title = h1_match.group(1).strip()
            # If a new H1 starts, it's a new top-level section
            current_section = {"title": title, "content": "", "subsections": []}
            sections_data.append(current_section)
            current_subsection = None # Reset lower levels
            current_sub_subsection = None
        elif h2_match and current_section:
            title = h2_match.group(1).strip()
            # If a new H2 starts, it's a new subsection within the current H1
            current_subsection = {"title": title, "content": "", "sub_subsections": []}
            current_section["subsections"].append(current_subsection)
            current_sub_subsection = None # Reset lower level
        elif h3_match and current_subsection:
            title = h3_match.group(1).strip()
            # If a new H3 starts, it's a new sub_subsection within the current H2
            current_sub_subsection = {"title": title, "content": ""}
            current_subsection["sub_subsections"].append(current_sub_subsection)
        else:
            # This line is content. Append it to the deepest active section/subsection.
            if current_sub_subsection:
                current_sub_subsection["content"] += line + "\n"
            elif current_subsection:
                current_subsection["content"] += line + "\n"
            elif current_section:
                current_section["content"] += line + "\n"
            # If content appears before any heading, it will be skipped by this logic.
            # You might want to add a "preamble" or "document_intro" section if that's a concern.

    # Post-processing: Clean up content (remove excessive newlines, leading/trailing whitespace)
    for section in sections_data:
        section["content"] = section["content"].strip()
        for subsection in section.get("subsections", []):
            subsection["content"] = subsection["content"].strip()
            for sub_subsection in subsection.get("sub_subsections", []):
                sub_subsection["content"] = sub_subsection["content"].strip()

    return sections_data

# --- Example Usage ---

# Write the main function to read the PDF and convert it to markdown

if __name__ == "__main__":
    # Read the PDF and convert it to markdown
    tic = time.time()
    
    # Read the file using LLama Parse, and save to markdown
    read_as_markdown(file_name)

    # Assume this markdown_file_path is the output from LlamaParse's markdown conversion
    markdown_file_path = extracted_name + ".md"    # This should exist from your LlamaParse run

    if not os.path.exists(markdown_file_path):
        print(f"Error: Markdown file not found at '{markdown_file_path}'")
    else:
        with open(markdown_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()

        # Get the document title from the filename (or you could extract from the markdown itself)
        document_title = os.path.splitext(os.path.basename(markdown_file_path))[0]
        
        # Preprocess the markdown
        processd_markdown = pre_process_llamaparse_markdown(markdown_content)
        # Parse the markdown content
        extracted_sections_json = parse_markdown_to_sections(processd_markdown)

        # Wrap it in the desired top-level JSON structure
        final_json_output = {
            "document_title": document_title,
            "sections": extracted_sections_json
        }

        # Save the structured data to a JSON file
        output_json_file_path = extracted_name + ".json"
        with open(output_json_file_path, 'w', encoding='utf-8') as f:
            json.dump(final_json_output, f, indent=4, ensure_ascii=False)

        print(f"Sections extracted and saved to '{output_json_file_path}'")

        # Example of how to access content for a specific section
        # This part would require knowing the exact title or a pattern.
        # For instance, finding "Introduction"
        # for section in final_json_output["sections"]:
        #     if "Introduction" in section["title"]:
        #         print(f"\nContent of Introduction:\n{section['content']}")
        #         break
    toc = time.time()
    print(f"Total time taken: {toc - tic} seconds")
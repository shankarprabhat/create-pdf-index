import re
from collections import Counter
import json
import os

# Your existing parse_regulatory_markdown_to_sections_fixed and pre_process_llamaparse_markdown here...

def pre_process_llamaparse_markdown_with_header_footer_removal_and_robust_page_breaks(
    markdown_text, 
    page_delimiter_base="---PAGE_BREAK___", # Base string for the delimiter
    header_footer_threshold_percentage=0.75, # e.g., 75% of pages
    header_footer_max_words=10 # Heuristic: headers/footers usually short
):
    # Regex to find the page delimiter, allowing for page number and surrounding text/whitespace
    # It captures the full line containing the page break, so we can clean it later.
    page_delimiter_regex = re.compile(rf'.*{re.escape(page_delimiter_base)}\d*.*', re.IGNORECASE)

    # Split the document into lines first to easily iterate and clean
    lines = markdown_text.split('\n')
    
    # Identify page break lines and store their indices
    page_break_line_indices = [i for i, line in enumerate(lines) if page_delimiter_regex.search(line)]

    # If no page breaks detected, treat as a single page or handle accordingly
    if not page_break_line_indices:
        print("Warning: No distinct page breaks found. Treating document as a single page for header/footer analysis.")
        pages_content = [lines] # List containing one list of lines
    else:
        # Reconstruct pages based on detected page break lines
        pages_content = []
        start_idx = 0
        for pb_idx in page_break_line_indices:
            pages_content.append(lines[start_idx:pb_idx])
            start_idx = pb_idx + 1 # Start next page after the page break line
        pages_content.append(lines[start_idx:]) # Add the last page

    # --- Header/Footer Identification (from previous logic) ---
    header_candidates = Counter()
    footer_candidates = Counter()
    
    num_pages = len(pages_content)
    if num_pages == 0: return "" # Handle empty document
    
    header_footer_threshold = num_pages * header_footer_threshold_percentage
    
    for page_lines_list in pages_content:
        # Clean each page's lines: strip whitespace and remove empty lines for analysis
        cleaned_page_lines = [line.strip() for line in page_lines_list if line.strip()]
        
        if len(cleaned_page_lines) > 0:
            for i in range(min(3, len(cleaned_page_lines))): # Check first N lines
                header_candidates[cleaned_page_lines[i]] += 1
            
            for i in range(max(0, len(cleaned_page_lines) - 3), len(cleaned_page_lines)): # Check last N lines
                footer_candidates[cleaned_page_lines[i]] += 1

    common_headers = {
        h for h, count in header_candidates.items() 
        if count >= header_footer_threshold and len(h.split()) < header_footer_max_words
    }
    common_footers = {
        f for f, count in footer_candidates.items() 
        if count >= header_footer_threshold and len(f.split()) < header_footer_max_words
    }
    
    # --- Main Processing Loop ---
    processed_lines = []
    
    for line_idx, line in enumerate(lines):
        stripped_line = line.strip()

        # 1. Handle lines containing the page delimiter
        if page_delimiter_regex.search(line):
            # This line contains the page break. We want to replace it with a clean page break marker
            # if we are actually splitting by pages for the downstream processing,
            # or just remove it if we just want cleaned markdown.
            # For header/footer removal, we usually just want to remove the full line.
            # If you still want a clean page break for other reasons, uncomment the next line:
            # processed_lines.append(page_delimiter_base.replace('___', '')) # e.g., ---PAGE_BREAK---
            continue # Skip this line as it's a page break marker with attached text

        # 2. Check if the line matches a common header or footer pattern
        if stripped_line in common_headers or stripped_line in common_footers:
            continue # Skip this line

        # 3. Apply your existing heading correction rules (from previous pre_process_llamaparse_markdown)
        # Ensure these are robust enough not to accidentally convert headers/footers that were NOT removed
        # but were very consistently formatted.
        
        # If LlamaParse makes a lettered subsection into an H2
        match_h2_lettered = re.match(r'^##\s*\(([a-z])\)\s*(.*)', line)
        if match_h2_lettered:
            processed_lines.append(f"({match_h2_lettered.group(1)}) {match_h2_lettered.group(2)}")
            continue

        # If LlamaParse makes a numbered sub-subsection into an H3
        match_h3_numbered = re.match(r'^###\s*\(([0-9])\)\s*(.*)', line)
        if match_h3_numbered:
            processed_lines.append(f"({match_h3_numbered.group(1)}) {match_h3_numbered.group(2)}")
            continue

        # If LlamaParse incorrectly makes a main section into an H2 instead of H1
        match_h2_section = re.match(r'^##\s*(§\s*\d+\.\d+)\s*(.*)', line)
        if match_h2_section:
            processed_lines.append(f"# {match_h2_section.group(1)} {match_h2_section.group(2)}")
            continue

        # If none of the above, keep the line
        processed_lines.append(line)

    return "\n".join(processed_lines)

# --- Example Usage (modified) ---
# Ensure you configure LlamaParse with `page_separator` that includes `{pageNumber}`
# Example LlamaParse initialization:
# parser = LlamaParse(
#     api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
#     result_type="markdown",
#     page_separator="---PAGE_BREAK__{pageNumber}---", # This will be the base delimiter
#     system_prompt_append=(
#         "Prioritize '§ X.X' as the highest level heading (level 1). "
#         "Lines starting with '(a)', '(b)', '(c)' should always be treated as nested subsections "
#         "under the nearest '§ X.X' section, and should not be standalone headings. "
#         "Lines starting with '(1)', '(2)', '(3)' should always be treated as sub-subsections "
#         "under the nearest '(a)/(b)/...' subsection."
#     )
# )
# documents = parser.load_data(file_path="your_input_document.pdf")
# raw_llamaparse_markdown = documents[0].text

# For demonstration, simulating the problematic LlamaParse output
raw_llamaparse_markdown_problematic = """
(n) Assent means a child's affirmative agreement to participate in a clinical investigation. Mere failure to object should not, absent affirmative agreement, be construed as assent.

21 CFR 50.23(d)(4) (enhanced display) page 8 of 17---PAGE_BREAK__9---21 CFR Part 50 (up to date as of 5/02/2025)

# § 50.3 Definitions
This is content for section 50.3.
"""

# Define the base delimiter used in LlamaParse
PAGE_DELIMITER_BASE = "---PAGE_BREAK__" # Note the double underscore for consistency

# --- Main script flow ---
# 1. Save raw LlamaParse output
intermediate_markdown_file_path = "intermediate_llamaparse_output.md"
with open(intermediate_markdown_file_path, 'w', encoding='utf-8') as f:
    f.write(raw_llamaparse_markdown_problematic)
print(f"Raw LlamaParse (or initial) markdown saved to '{intermediate_markdown_file_path}'")

# 2. Apply robust pre-processing (including header/footer removal and page break handling)
cleaned_markdown_content = pre_process_llamaparse_markdown_with_header_footer_removal(
    raw_llamaparse_markdown_problematic, 
    page_delimiter_base=PAGE_DELIMITER_BASE
)

# 3. Save the pre-processed markdown
preprocessed_markdown_file_path = "preprocessed_markdown_for_json_parser.md"
with open(preprocessed_markdown_file_path, 'w', encoding='utf-8') as f:
    f.write(cleaned_markdown_content)
print(f"Pre-processed markdown saved to '{preprocessed_markdown_file_path}'")

# 4. Parse the cleaned markdown content into JSON
document_title = "Example_CFR_Section_Parsed_Fixed" # Or derive from your PDF filename
extracted_sections_json = parse_regulatory_markdown_to_sections_fixed(cleaned_markdown_content)

# 5. Wrap it in the desired top-level JSON structure and save
final_json_output = {
    "document_title": document_title,
    "sections": extracted_sections_json
}

output_json_file_path = "extracted_regulatory_sections_from_markdown_fixed.json"
with open(output_json_file_path, 'w', encoding='utf-8') as f:
    json.dump(final_json_output, f, indent=4, ensure_ascii=False)

print(f"Final structured JSON saved to '{output_json_file_path}'")
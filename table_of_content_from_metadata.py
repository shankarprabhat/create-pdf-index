# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 21:01:00 2025

@author: Admin
"""

import json

def build_toc(headings_data):
    # Filter out heading_level 0 as they appear to be page/document metadata
    # Also create a map for quick lookup by node_id for parent/child linking
    heading_map = {h['node_id']: h for h in headings_data if h.get('heading_level') != 0}

    # Initialize a structure for the TOC (e.g., a list of dictionaries)
    toc = []

    # Identify true top-level sections (heading_level 1 with no meaningful parent in the TOC)
    # We explicitly check that the parent (if it exists) is NOT a level 0 heading.
    top_level_headings = []
    for h in heading_map.values():
        if h['heading_level'] == 1:
            parent_id = h.get('parent_node_id')
            if parent_id is None: # Truly no parent, definitely a top-level
                top_level_headings.append(h)
            else:
                parent_heading = heading_map.get(parent_id)
                # If parent exists and is NOT level 0, then this is a subsection of that parent.
                # If parent is level 0, we treat this current heading as a top-level.
                if parent_heading and parent_heading.get('heading_level') != 0:
                    # This heading has a valid, non-zero-level parent, so it's not a top-level for our TOC
                    continue
                else:
                    top_level_headings.append(h)


    # Sort top-level headings by page_label and then by their original order (approximate)
    # Using 'heading_id' for secondary sort if it's numerical and sequential
    top_level_headings.sort(key=lambda x: (int(x.get('page_label', 0)), x.get('heading_id', '')))

    for top_heading in top_level_headings:
        toc.append(parse_section(top_heading, heading_map))
    return toc

def parse_section(current_heading, heading_map):
    section_entry = {
        "title": current_heading["section_title"],
        "page": current_heading["page_label"],
        "level": current_heading["heading_level"],
        "subsections": []
    }

    # Find children (subsections) of the current heading
    # Children will have a heading_level one greater than the parent
    # and their parent_node_id will match the current heading's node_id.
    children = [
        h for h in heading_map.values()
        if h.get('parent_node_id') == current_heading['node_id'] and
           h.get('heading_level') == current_heading['heading_level'] + 1
    ]

    # Sort children to maintain order
    children.sort(key=lambda x: (int(x.get('page_label', 0)), x.get('heading_id', ''))) # Sort by page and heading_id

    for child in children:
        section_entry["subsections"].append(parse_section(child, heading_map))

    return section_entry

def print_toc(toc_list, indent_level=0):
    for entry in toc_list:
        # Use an appropriate symbol or just indentation
        prefix = "  " * indent_level
        print(f"{prefix}{entry['title']} (Page: {entry['page']})")
        if entry["subsections"]:
            print_toc(entry["subsections"], indent_level + 1)

# load the json_data from file
fname = 'extracted_nodes_ich-gcp-r2-step-5.json'
# fname = 'extracted_nodes_AZD9291.json'
# fname = 'extracted_nodes_NITLT01.json'

with open(fname, 'r') as f:
    json_data = json.load(f)

# Build the table of contents
table_of_contents = build_toc(json_data)

# Print the table of contents
print("---")
print("Extracted Table of Contents:")
print("---")
print_toc(table_of_contents,3)
print("---")
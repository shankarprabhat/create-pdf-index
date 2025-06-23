from llama_parse import LlamaParse


parser = LlamaParse(
   api_key="llx-1kYzRnzJoUdF5rNqFs6qPBgBqxm5uFnF4b5IZMYooSzNAGo2",  # if you did not create an environmental variable you can set the API key here
   result_type="markdown",  # "markdown" and "text" are available
   )

file_name = "ich-gcp-r2-step-5.pdf"
extra_info = {"file_name": file_name}

with open(f"./{file_name}", "rb") as f:
   # must provide extra_info with file_name key with passing file object
   documents = parser.load_data(f, extra_info=extra_info)

# with open('output.md', 'w') as f:
   # print(documents, file=f)

# Write the output to a file
with open("output.md", "w", encoding="utf-8") as f:
   for doc in documents:
       f.write(doc.text)
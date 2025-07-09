import requests
import os
import time
import json # Import json for pretty printing
import dotenv # Import dotenv to load environment variables from a .env file

# Load environment variables from .env file
dotenv.load_dotenv()
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")

# Ensure your API key is set as an environment variable
# LLAMA_CLOUD_API_KEY = os.environ.get("LLAMA_CLOUD_API_KEY")

if not LLAMA_CLOUD_API_KEY:
    print("Error: LLAMA_CLOUD_API_KEY environment variable not set.")
    exit()

# Replace with the actual job_id you received
job_id = "7e0fd391-f00e-4567-af25-c5b10b93d057"

base_url = "https://api.cloud.llamaindex.ai/api/v1/parsing/job/"
headers = {
    "accept": "application/json",
    "Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}"
}

def get_job_status(job_id):
    """Fetches the status of a LlamaParse job."""
    url = f"{base_url}{job_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job status for {job_id}: {e}")
        return None

def get_job_result(job_id, result_type="markdown"):
    """Fetches the result (markdown or json) of a successful LlamaParse job."""
    url = f"{base_url}{job_id}/result/{result_type}"
    headers_result = {
        "accept": "application/json", # Even for markdown, they often return a JSON object with a 'markdown' key
        "Authorization": f"Bearer {LLAMA_CLOUD_API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers_result)
        response.raise_for_status()
        return response.json() # Returns a dict like {'markdown': '...', 'job_metadata': {...}}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching job result for {job_id} (type: {result_type}): {e}")
        return None

print(f"--- Checking Status for Job ID: {job_id} ---")
job_info = get_job_status(job_id)

if job_info:
    print(f"Current Status: {job_info.get('status')}")
    print(f"Error Message (if any): {job_info.get('error')}") # Look for this!
    print(f"Job Type: {job_info.get('job_type')}") # This might show 'json' even if you requested markdown

    if job_info.get('status') == 'SUCCESS':
        print("\n--- Attempting to retrieve Markdown result ---")
        md_result = get_job_result(job_id, result_type="markdown")
        if md_result and 'markdown' in md_result:
            print("Markdown Result (first 500 chars):\n")
            print(md_result['markdown'][:500])
            with open(f"retrieved_job_{job_id}.md", "w", encoding="utf-8") as f:
                f.write(md_result['markdown'])
            print(f"\nFull Markdown result saved to retrieved_job_{job_id}.md")
        else:
            print("Failed to retrieve Markdown result or result was empty.")

        # You can also try retrieving the JSON result to see what's there
        print("\n--- Attempting to retrieve JSON result (for comparison) ---")
        json_result = get_job_result(job_id, result_type="json")
        if json_result and 'json' in json_result:
            print("JSON Result (first 500 chars):\n")
            print(json.dumps(json_result['json'], indent=2)[:500])
            with open(f"retrieved_job_{job_id}.json", "w", encoding="utf-8") as f:
                json.dump(json_result['json'], f, indent=4, ensure_ascii=False)
            print(f"\nFull JSON result saved to retrieved_job_{job_id}.json")
        else:
            print("Failed to retrieve JSON result or result was empty.")

    elif job_info.get('status') == 'FAILED':
        print(f"\nJob FAILED. Error details from LlamaParse: {job_info.get('error_message', 'No specific error message provided.')}")
        print("This is the 'log' or diagnostic information you're looking for directly from LlamaParse.")
    else:
        print("\nJob is still pending or processing. You might need to wait and re-run this script.")
else:
    print("Could not retrieve job information.")
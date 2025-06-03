### Ground Truth Data Generation Script

This script (`scripts/generate_ground_truth.py` - assuming this is the name) is used to generate a dataset of potential user questions based on the text extracted from the NITW documents (`database.json`). It leverages a Large Language Model (LLM) to create realistic queries that a student might ask after reviewing the document content. This "ground truth" data is valuable for evaluating the performance of the RAG pipeline's search and answer generation components.

#### Functionality

-   **Loads Processed Data:** Reads the data and extracted text from the `database.json` file.
-   **LLM Question Generation:** For each document, it constructs a prompt using the document's title and extracted text (`info`). This prompt instructs the LLM to generate a specific number (currently 5) of relevant questions based on the provided context.
-   **LLM Interaction:** Sends the prompt to a configured LLM (using either Google Gemini or an OpenAI-compatible endpoint like OpenRouter).
-   **Checkpointing:** Saves the raw LLM responses (the generated questions) along with the document URL to a JSON file (`checkpoint_results.json`) after processing each document. This allows resuming the process if interrupted.
-   **Data Structuring:** Parses the LLM's output (expected to be a JSON array of questions) and structures the data into a list of `(question, url)` pairs.
-   **CSV Output:** Saves the final structured ground truth data as a CSV file (`ground-truth-data.csv`) with 'question' and 'url' columns.

#### How It Works

The script iterates through each document in `database.json`. For every document:

1.  It formats a prompt containing the document's title and text.
2.  It calls the configured LLM with this prompt.
3.  It receives the LLM's response (a string expected to contain a JSON array of questions).
4.  It saves the raw response and the document URL to `checkpoint_results.json`.
5.  After processing all documents, it loads `checkpoint_results.json`, parses the question strings, and formats them into a list of `(question, url)` pairs.
6.  This list is then saved as `ground-truth-data.csv`.


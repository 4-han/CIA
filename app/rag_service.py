# CIA/app/rag_service.py
import json
import asyncio
from openai import OpenAI
# Correct import for google.generativeai
import google.generativeai as genai
import minsearch
import logging

# Ensure these are imported from config
from config import DATA_FILE, GOOGLE_API_KEY, LLM_MODEL, OPENAI_API_KEY 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


try:
    with open(DATA_FILE, 'rt', encoding='utf-8') as f_in:
        documents = json.load(f_in)
    logging.info(f"Loaded {len(documents)} documents from {DATA_FILE}")
except FileNotFoundError:
    logging.error(f"Data file not found: {DATA_FILE}. Please ensure it exists. Check DATA_FILE in .env")
    documents = [] 
except json.JSONDecodeError:
    logging.error(f"Error decoding JSON from {DATA_FILE}. Check JSON format.")
    documents = []
except Exception as e:
    logging.error(f"An unexpected error occurred loading data from {DATA_FILE}: {e}")
    documents = []



def chunk_data(raw_doc, chunk_size=4999, overlap=100):
    """Chunks the 'info' field of documents."""
    def chunk_content(content, chunk_size=chunk_size, overlap=overlap):
        chunks = []
        start = 0
        
        if not isinstance(content, str):
             logging.warning(f"Skipping chunking for non-string content: {content}")
             return [str(content)] 


        if chunk_size <= 0:
            logging.error("Chunk size must be positive.")
            return [content] 
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            if overlap >= chunk_size:
                 start = end 
            else:
                 start = end - overlap
        return chunks

    chunked_data = []
    if not documents:
        logging.warning("No documents loaded, skipping chunking.")
        return []


    for doc in raw_doc:
        url = doc.get('url', 'N/A')
        date = doc.get('date', 'N/A')
        title = doc.get('title', 'Untitled')
        info = doc.get('info', '') 

        content_chunks = chunk_content(info, chunk_size, overlap)

        if not content_chunks and info:
             content_chunks = [info]
        elif not content_chunks and not info:
             content_chunks = [""] 

        for i, chunk in enumerate(content_chunks):
             chunked_data.append({
                'url': url,
                'date': date,
                'title': title,
                'info': chunk 
            })

    logging.info(f"Chunked data into {len(chunked_data)} chunks.")
    return chunked_data

chunked_documents = chunk_data(documents)
Index = minsearch.Index(
    text_fields=["title", "info"],
    keyword_fields=[] 
)
if chunked_documents:
    Index.fit(chunked_documents)
    logging.info("Minsearch index built.")
else:
    logging.warning("No chunked documents to build minsearch index.")


# llm_client_gemini = None
# if GOOGLE_API_KEY:
#     try:
#         # Use google.generativeai.Client
#         llm_client_gemini = genai.Client(api_key=GOOGLE_API_KEY) 
#         logging.info("Gemini client initialized.")
#     except Exception as e:
#          logging.error(f"Failed to initialize Gemini client: {e}")
# else:
#     logging.warning("GOOGLE_API_KEY not found, Gemini client not initialized.")

#penAI Client (currently commented out based on your previous version)
llm_client_openai = None
if OPENAI_API_KEY:
    try:
        clientOI = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENAI_API_KEY
        )
        logging.info("OpenAI/OpenRouter client initialized.")
    except Exception as e:
         logging.error(f"Failed to initialize OpenAI/OpenRouter client: {e}")
else:
    logging.warning("OPENAI_API_KEY not found, OpenAI client not initialized.")




def build_prompt(query, search_results):
    prompt_template = """You are an AI assistant designed to help students of NIT Warangal (NITW) by answering their questions accurately and responsibly.

        You are provided with CONTEXT retrieved from trusted NITW sources. Your job is to:

        1.  Base your answer *primarily* on the provided CONTEXT. Synthesize information from the context to address the user's query as accurately as possible.
        2.  Do NOT use any outside or prior knowledge. Your response must be derived *solely* from the provided context.
        3.  **Handling Insufficient or Loosely Related Context:**
            *   If the context does not contain a direct or complete answer to the query, do *not* invent information.
            *   Instead, summarize the most relevant information found in the context related to the query.
            *   If the context is only loosely related or minimal, acknowledge the query and provide the relevant context snippets or simply list the source URL(s) as the best available information based on the text provided.
            *   Do *not* use the phrase "I could not find a verified answer to that in the available information."
        4.  **Crucially:** Do NOT hallucinate. Only state facts or information that are explicitly mentioned or clearly inferable *from the provided context*.
        5.  ALWAYS cite the source(s) used by including the URL(s) at the end of your response.

        Now, answer the following question:{query}
        URL: {url}

        CONTEXT: {context}

        INSTRUCTIONS:
        - Only use facts and information derived *strictly* from the context.
        - Do not assume, generate, or state information not backed by the context.
        - If a direct answer isn't possible from the context, provide relevant summaries or snippets from the context instead.
        - Make your response clear and concise.
        (SOURCE: {url}""".strip()


    context = ""

    sources = set()
    for doc in search_results:
        context += f"title: {doc.get('title', 'Untitled')}\ninfo: {doc.get('info', 'No info')}\n\n"
        sources.add(doc.get('url', 'N/A')) 

    sources_str = "\n".join(list(sources)) 

    # Format the final prompt
    prompt = prompt_template.format(url=sources_str, context=context, query = query).strip()

    logging.info(f"Built prompt for query: '{query[:50]}...'")
    return prompt


async def search_documents(query, num_results=5):
    """Searches the minsearch index asynchronously."""
    if not chunked_documents:
        logging.warning("Cannot search, no documents are indexed.")
        return []

    boost = {"title": 1, 'info': 1}
    results = await asyncio.to_thread(Index.search, query=query, boost_dict=boost, num_results=num_results)
    logging.info(f"Search found {len(results)} results for query: '{query[:50]}...'")
    return results


async def generate_answer(prompt, model=LLM_MODEL):
    # """Generates an answer using the configured Gemini LLM client asynchronously."""
    # if llm_client_gemini is None:
    #     logging.error("LLM client is not initialized. Cannot generate answer.")
    #     return "Error: Language model is not available (API key missing?)."

    # try:
    #     # The generate_content method is synchronous, wrap it in asyncio.to_thread
    #     response = await asyncio.to_thread(
    #         llm_client_gemini.models.generate_content, # Pass the method
    #         model=model,                            # Pass model as a keyword argument
    #         contents=prompt                         # Pass contents as a keyword argument
    #     )

    #     # Access the generated text from the response object
    #     answer = response.text
    #     logging.info(f"Generated answer for prompt: '{prompt[:50]}...'")
    #     return answer
    
    response = clientOI.chat.completions.create(
        model="thudm/glm-z1-32b:free",  # Or any model from OpenRouter
        messages=[
            {"role": "user", "content": prompt }
        ]
    )
    return response.choices[0].message.content 
    # except Exception as e:
    #     logging.error(f"Error calling Gemini API: {e}")
    #     # Attempt to get more detailed error if available (can vary by exception type)
    #     error_detail = str(e)
    #     # If it's a google.api_core.exceptions, you might get more info
    #     if hasattr(e, 'message'):
    #          error_detail = e.message
    #     # You might want to log the full exception for debugging in logs

    #     return f"Sorry, I couldn't generate an answer due to a Gemini API error: {error_detail}"


# Main RAG pipeline function
async def rag_pipeline(query):
    """Runs the complete RAG pipeline for a given query."""
    logging.info(f"Starting RAG pipeline for query: {query}")
    search_results = await search_documents(query)
    if not search_results:
        logging.warning("No relevant documents found for RAG.")
        return "I couldn't find any relevant information in the available documents to answer your question."

    prompt = build_prompt(query, search_results)
    answer = await generate_answer(prompt)
    logging.info(f"RAG pipeline finished for query: {query}")
    return answer

if __name__ == "__main__":
    async def test_rag():

        query = "Tell me about NIT Warangal"
        print(f"Running RAG for query: '{query}'")
        response = await rag_pipeline(query)
        print("\nRAG Response:")
        print(response)

        print("-" * 20) 

        query_no_info = "can you list down some interesting events coming up or that has happened ?" 
        print(f"\nRunning RAG for query: '{query_no_info}'")
        response_no_info = await rag_pipeline(query_no_info)
        print("\nRAG Response (No Info):")
        print(response_no_info)

    #asyncio.run(test_rag())
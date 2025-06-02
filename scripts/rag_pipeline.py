import json
import argparse
import asyncio
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from openai import OpenAI
from google import genai
import minsearch


parser = argparse.ArgumentParser(description='RAG (Retrieval-Augmented Generation) pipeline for NIT Warangal')
parser.add_argument('--query', type=str, default='tell us more about nit warangal', 
                    help="Query to search and get information from the documents")
args = parser.parse_args()


with open('../data/database.json', 'rt') as f_in:
    documents = json.load(f_in)


index_name = "nitw-cia"


client_gemini = genai.Client()
client_openai = OpenAI(base_url="https://openrouter.ai/api/v1")







# Prompt builder for LLM
def prompt_builder(query, search_results):
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
        - At the end of your answer, include a reference to the source like:
        (SOURCE: {url})""".strip()
            
            
    context = ""
    sources = ""
    for doc in search_results:
        context = context + f"title: {doc['title']}\ninfo: {doc['info']}\n\n"
        sources += f"url: {doc['url']}\n"
            
        
    prompt = prompt_template.format(url=sources, context=context, query = query).strip()

# Chunk data for Elasticsearch
def chunk_data(raw_doc, chunk_size=4999, overlap=100):
    def chunk_content(content, chunk_size=4999, overlap=100):
        chunks = []
        start = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            chunks.append(chunk)
            start = end - overlap
        return chunks

    chunked_data = []
    for doc in raw_doc:
        content_chunks = chunk_content(doc['info'], chunk_size, overlap)
        for i, chunk in enumerate(content_chunks):
            chunked_data.append({
                'url': doc['url'],
                'date': doc['date'],
                'title': doc['title'],
                'info': chunk
            })
    
    return chunked_data

data_chunk = chunk_data(documents)




Index = minsearch.Index(
    text_fields=["title", "info"],
    keyword_fields=[]
)
Index.fit(chunk_data)

async def search(query):
    boost = {"title": 1, 'info': 1}
    results = await asyncio.to_thread(Index.search, query=query, boost_dict=boost, num_results=5)
    return results


async def llm_OpenAI(prompt):
    response = await asyncio.to_thread(client_openai.chat.completions.create,
                                        model="mistralai/mixtral-8x7b-instruct",
                                        messages=[{"role": "user", "content": prompt}])
    
    return response.choices[0].message.content

# Gemini LLM function
async def llm_gemini(prompt):
    response = await asyncio.to_thread(client_gemini.models.generate_content,
                                        model="gemini-2.0-flash-lite",
                                        contents=prompt)
    
    return response.text


async def rag(query):
    search_results = await search(query)
    prompt = prompt_builder(query, search_results)
    answer = await llm_gemini(prompt)
    return answer


async def main():

    
    await index_chunked_data()
    

    llm_response = await rag(args.query)
    print(llm_response)

if __name__ == "__main__":
    asyncio.run(main())

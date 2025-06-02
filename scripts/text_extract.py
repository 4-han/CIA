import json
import os
import pandas as pd
import requests
import fitz
from io import BytesIO
from tqdm.auto import tqdm
import re


LINKS_FILE = "../data/pdf_links.json"
DATABASE_FILE = "../data/database.json"

os.makedirs(os.path.dirname(LINKS_FILE), exist_ok=True)


print(f"[INFO] Loading PDF links from {LINKS_FILE}...")
with open(LINKS_FILE, 'rt') as f_out:
    documents = json.load(f_out)
df = pd.DataFrame(documents)
df = df.to_dict(orient='records')

print("[INFO] Extracting text from PDF links...")

for doc in tqdm(df):
    try:
        
        response = requests.get(doc['url'])
        response.raise_for_status()

        
        pdf_file = BytesIO(response.content)

        
        pdf = fitz.open(stream=pdf_file, filetype="pdf")
        text = ""
        for page in pdf:
            text += page.get_text()
        pdf.close()

        
        doc["info"] = text.strip()
        print(f"[INFO] Successfully extracted text from the PDF.")

    except Exception as e:
        
        doc["info"] = f"Error extracting text: {e}"
        print(f"[ERROR] Failed to extract text from PDF: {e}")
        
print("[INFO] Cleaning the extracted text...")
def clean_text(raw_text):
    text = re.sub(r'\n\s*\n+', '\n\n', raw_text)  
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)  
    text = re.sub(r' +', ' ', text)  
    return text


for doc in df:
    doc["info"] = clean_text(doc["info"])

print(f"[INFO] Saving the cleaned data to {DATABASE_FILE}...")
with open(DATABASE_FILE, "w", encoding="utf-8") as f_in:
    json.dump(df, f_in, indent=4, ensure_ascii=False)

print(f"[INFO] Processed data successfully saved to {DATABASE_FILE}")

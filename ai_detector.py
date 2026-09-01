import os
os.environ["HF_HUB_OFFLINE"] = "0"
os.environ["HF_DATASETS_OFFLINE"] = "0"
import torch
from transformers import pipeline
import sys

def detect_ai(file_path):
    print("Loading AI detector model...")
    # Using a popular open-source ChatGPT detector
    pipe = pipeline("text-classification", model="Hello-SimpleAI/chatgpt-qa-detector-roberta", device=0 if torch.cuda.is_available() else -1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Model has a max token limit. We'll split the text into chunks of ~150 words.
    words = text.split()
    chunk_size = 150
    chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
    
    ai_scores = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip(): continue
        try:
            result = pipe(chunk)
            label = result[0]['label']
            score = result[0]['score']
            
            # Label is usually 'ChatGPT' or 'Human'
            if label.lower() == 'chatgpt' or label.lower() == 'fake':
                ai_scores.append(score)
            else:
                ai_scores.append(1.0 - score)
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
            
    if not ai_scores:
        print("Could not calculate score.")
        return
        
    avg_ai_score = sum(ai_scores) / len(ai_scores)
    print(f"--- RESULTS ---")
    print(f"AI Generated Score: {avg_ai_score * 100:.2f}%")
    if avg_ai_score < 0.60:
        print("PASS! The document is sufficiently human-like.")
    else:
        print("FAIL. The document is too AI-like.")
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ai_detector.py <file_path>")
        sys.exit(1)
    detect_ai(sys.argv[1])

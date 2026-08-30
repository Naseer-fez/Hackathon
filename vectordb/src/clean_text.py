import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Applies conservative text cleaning to the extracted text."""
    if not isinstance(text, str):
        return ""
        
    # 1. Normalize line breaks (replace multiple line breaks with double line break)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 2. Normalize whitespace (replace multiple spaces with a single space)
    # But keep line breaks intact
    text = re.sub(r'[ \t\r\f\v]+', ' ', text)
    
    # 3. Fix simple OCR spacing issues where letters are separated by spaces (e.g. "f l o w")
    # This is conservative: only fix single letters separated by space that form a word of at least 3 letters
    def fix_ocr_spacing(match):
        return match.group(0).replace(' ', '')
        
    text = re.sub(r'(?:\b[a-zA-Z]\s){2,}\b[a-zA-Z]\b', fix_ocr_spacing, text)
    
    # 4. Remove unprintable control characters except standard ones (\n, \t)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    return text.strip()

def process_dataframe_text(df: pd.DataFrame) -> pd.DataFrame:
    """Applies text cleaning to the entire dataframe."""
    logger.info("Cleaning text...")
    df = df.copy()
    
    # Keep original text for debugging
    df['original_text'] = df['extracted_text']
    
    # Apply cleaning
    df['cleaned_text'] = df['extracted_text'].apply(clean_text)
    
    # Filter out records that became empty after cleaning
    valid_mask = df['cleaned_text'].str.strip() != ''
    valid_records = valid_mask.sum()
    logger.info(f"Valid records after cleaning: {valid_records}")
    
    df = df[valid_mask]
    return df

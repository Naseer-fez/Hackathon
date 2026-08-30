import pandas as pd
import logging

logger = logging.getLogger(__name__)

def load_dataset(csv_path: str) -> pd.DataFrame:
    """Loads the extracted document CSV and performs basic validation."""
    logger.info(f"Loading CSV from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
        logger.info(f"Rows loaded: {len(df)}")
        
        # Check for required columns
        required_cols = ['doc_id', 'file_name', 'folder_category', 'page_number', 'total_pages', 'extracted_text']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in CSV: {missing_cols}")
            
        # Basic stats
        logger.info(f"Number of unique documents: {df['doc_id'].nunique()}")
        
        # Filter out rows with completely empty text
        initial_count = len(df)
        df['extracted_text'] = df['extracted_text'].fillna('')
        df = df[df['extracted_text'].str.strip() != '']
        if len(df) < initial_count:
            logger.warning(f"Dropped {initial_count - len(df)} rows with empty text.")
            
        return df
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

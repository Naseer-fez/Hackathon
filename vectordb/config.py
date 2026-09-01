import os
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseConfig(BaseModel):
    """
    Configuration for the Vector Database.
    Reads from the centralized backend/config/config.yaml
    Allows seamless toggling between databases using the active_db flag in YAML.
    """
    active_db: str = Field(default="old")
    active_db_path: str = Field(default="D:\\Extras\\ES\\Final_Vector_DB")
    old_db_1_path: str = Field(default="D:\\Extras\\ES\\Old_DB_1")
    old_db_2_path: str = Field(default="D:\\Extras\\ES\\Old_DB_2")
    bis_data_path: str = Field(default="D:\\Extras\\ES\\Scrapiing\\Version2\\Final Data")
    collection_name: str = Field(default="bis_standards_collection")
    embedding_model: str = Field(default=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    @property
    def is_using_final_db(self) -> bool:
        """Check if we are pointing to the final vector DB."""
        return self.active_db == "final"

def load_config() -> DatabaseConfig:
    # Path to the main config.yaml
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "backend", "config", "config.yaml")
    yaml_path = os.path.abspath(yaml_path)
    
    cfg = DatabaseConfig()
    if os.path.exists(yaml_path):
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                vd_config = data.get("vector_database", {})
                
                # Update Pydantic model fields based on yaml
                cfg.active_db = vd_config.get("active_db", cfg.active_db)
                
                # Determine active path dynamically based on the active_db toggle
                if cfg.active_db == "final":
                    cfg.active_db_path = vd_config.get("final_db_path", cfg.active_db_path)
                elif cfg.active_db == "old":
                    # For legacy fallback, you may decide which legacy path is the 'primary' or handle them dynamically
                    # We will default it to old_db_1_path as the active one in fallback mode, 
                    # but the migrate script will still use both properties.
                    cfg.active_db_path = vd_config.get("old_db_1_path", cfg.old_db_1_path)

                cfg.old_db_1_path = vd_config.get("old_db_1_path", cfg.old_db_1_path)
                cfg.old_db_2_path = vd_config.get("old_db_2_path", cfg.old_db_2_path)
                cfg.bis_data_path = vd_config.get("bis_data_path", cfg.bis_data_path)
                cfg.collection_name = vd_config.get("collection_name", cfg.collection_name)
                
            logger.info(f"Loaded vector_database config from {yaml_path}. Active DB Mode: {cfg.active_db}")
        except Exception as e:
            logger.error(f"Failed to load yaml config from {yaml_path}: {e}")
    else:
        logger.warning(f"Config yaml not found at {yaml_path}. Using default configurations.")
        
    return cfg

config = load_config()

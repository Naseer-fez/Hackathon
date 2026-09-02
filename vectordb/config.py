import os
from pathlib import Path
import yaml
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

from backend.config.paths import (
    CONFIG_YAML_PATH,
    DATA_DIR,
    EMBEDDING_MODEL_PATH,
    PROJECT_ROOT,
    VECTORDB_CHROMA_DIR,
    VECTORDB_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class DatabaseConfig(BaseModel):
    """
    Configuration for the Vector Database.
    Reads from the centralized backend/config/config.yaml
    Allows seamless toggling between databases using the active_db flag in YAML.
    """
    active_db: str = Field(default="local")
    active_db_path: str = Field(default=str(VECTORDB_CHROMA_DIR))
    old_db_1_path: str = Field(default=str(VECTORDB_DIR))
    old_db_2_path: str = Field(default=str(VECTORDB_DIR))
    bis_data_path: str = Field(default=str(DATA_DIR))
    collection_name: str = Field(default="bis_standards_collection")
    embedding_model: str = Field(default=os.getenv("EMBEDDING_MODEL", str(EMBEDDING_MODEL_PATH)))

    @property
    def is_using_final_db(self) -> bool:
        """Check if we are pointing to the final vector DB."""
        return self.active_db in ("final", "local")

def load_config() -> DatabaseConfig:
    yaml_path = CONFIG_YAML_PATH
    cfg = DatabaseConfig()
    if yaml_path.exists():
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                vd_config = data.get("vector_database", {})
                
                cfg.active_db = vd_config.get("active_db", cfg.active_db)
                
                final_path = vd_config.get("final_db_path", cfg.active_db_path)
                old1_path = vd_config.get("old_db_1_path", cfg.old_db_1_path)
                old2_path = vd_config.get("old_db_2_path", cfg.old_db_2_path)
                bis_path = vd_config.get("bis_data_path", cfg.bis_data_path)

                def _resolve(p_str: str) -> str:
                    if not os.path.isabs(p_str):
                        return str(PROJECT_ROOT / p_str)
                    return p_str

                cfg.active_db_path = _resolve(final_path) if cfg.active_db in ("final", "local") else _resolve(old1_path)
                cfg.old_db_1_path = _resolve(old1_path)
                cfg.old_db_2_path = _resolve(old2_path)
                cfg.bis_data_path = _resolve(bis_path)
                cfg.collection_name = vd_config.get("collection_name", cfg.collection_name)
                
            logger.info(f"Loaded vector_database config from {yaml_path}. Active DB Mode: {cfg.active_db}")
        except Exception as e:
            logger.error(f"Failed to load yaml config from {yaml_path}: {e}")
    else:
        logger.warning(f"Config yaml not found at {yaml_path}. Using default configurations.")
        
    return cfg

config = load_config()

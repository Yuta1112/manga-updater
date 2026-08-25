from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseParser(ABC):
    """Base class for all manga site parsers"""
    
    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
    
    @abstractmethod
    def get_latest_chapter(self) -> Optional[Dict[str, str]]:
        """
        Get the latest chapter information from the manga page
        
        Returns:
            Dict with keys: 'latest_chapter', 'title', 'url'
            Or None if parsing failed
        """
        pass
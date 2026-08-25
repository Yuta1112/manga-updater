import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from .chapter import compare_chapters


class StateManager:
    """Manages the state of manga chapters to detect updates"""
    
    def __init__(self, state_file: str = "data/state.json"):
        self.state_file = state_file
        self.state_data = self.load_state()
    
    def load_state(self) -> Dict[str, Any]:
        """Load state from file, return empty dict if file doesn't exist"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARN] Could not load state file {self.state_file}: {e}. Starting with empty state.")
                return {}
        else:
            print(f"[INFO] State file {self.state_file} does not exist. Creating new state.")
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            return {}
    
    def save_state(self) -> bool:
        """Save current state to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state_data, f, ensure_ascii=False, indent=2)
            print(f"[INFO] State saved to {self.state_file}")
            return True
        except IOError as e:
            print(f"[ERROR] Could not save state to {self.state_file}: {e}")
            return False
    
    def get_latest_chapter(self, manga_name: str) -> Optional[str]:
        """Get the latest chapter recorded for a manga"""
        return self.state_data.get(manga_name, {}).get('latest_chapter')
    
    def update_manga(self, manga_name: str, latest_chapter: str, url: str) -> bool:
        """Update the latest chapter for a manga"""
        current_time = datetime.now().isoformat()
        
        if manga_name not in self.state_data:
            self.state_data[manga_name] = {}
        
        self.state_data[manga_name].update({
            'latest_chapter': latest_chapter,
            'url': url,
            'last_checked': current_time
        })
        
        return self.save_state()
    
    def has_updated(self, manga_name: str, current_chapter: str) -> tuple[bool, Optional[str]]:
        """Check if a manga has been updated since last check
        
        Returns:
            Tuple of (has_updated: bool, previous_chapter: Optional[str])
        """
        previous_chapter = self.get_latest_chapter(manga_name)
        
        if previous_chapter is None:
            # This is the first time checking this manga, don't consider it an update
            return False, None
        
        # Compare chapters reliably (第9話 < 第10話, etc.)
        comparison = compare_chapters(current_chapter, previous_chapter)
        if comparison is None:
            print(
                f"[WARN] {manga_name} → Unable to compare chapter: "
                f"previous={previous_chapter!r}, current={current_chapter!r}"
            )
            return False, previous_chapter

        if comparison > 0:
            return True, previous_chapter

        return False, previous_chapter
    
    def get_all_manga_names(self) -> list[str]:
        """Get all manga names in the state"""
        return list(self.state_data.keys())
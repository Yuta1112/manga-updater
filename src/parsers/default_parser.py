import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urljoin
from .base import BaseParser


class DefaultParser(BaseParser):
    """Default parser for common manga sites"""
    
    def __init__(self, name: str, url: str):
        super().__init__(name, url)
    
    def get_latest_chapter(self) -> Optional[Dict[str, str]]:
        """
        Try to find the latest chapter using common patterns
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"[ERROR] Failed to fetch {self.name}: HTTP {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Common selectors for latest chapter
            selectors = [
                'a[href*="chapter"], .chapter-link, [class*="chapter"], [id*="chapter"]',
                'a:contains("Chapter"), a:contains("chap"), a:contains("話"), a:contains("话")',
                '.latest-chapter, .newest, .recent, .update',
                '[href*="/ch"]',  # Links containing "ch"
            ]
            
            latest_chapter = None
            chapter_title = None
            chapter_url = None
            
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        
                        # Look for chapter-like patterns
                        chapter_match = re.search(r'(?:第|Ch|chap|Chapter|話|话)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                        if chapter_match:
                            chapter_num = chapter_match.group(1)
                            if latest_chapter is None or float(chapter_num) > float(latest_chapter):
                                latest_chapter = chapter_num
                                chapter_title = text
                                
                                # Get the URL for the chapter
                                href = element.get('href')
                                if href:
                                    chapter_url = urljoin(self.url, href)
                                else:
                                    chapter_url = self.url
                                break
                            
                        # Also check for simple numeric patterns like "120", "121", etc.
                        simple_match = re.search(r'^(\d+(?:\.\d+)?)$', text.strip())
                        if simple_match and len(text.strip()) >= 1:
                            chapter_num = simple_match.group(1)
                            if latest_chapter is None or float(chapter_num) > float(latest_chapter):
                                latest_chapter = chapter_num
                                chapter_title = f"Chapter {chapter_num}"
                                href = element.get('href')
                                if href:
                                    chapter_url = urljoin(self.url, href)
                                else:
                                    chapter_url = self.url
                                break
                except:
                    continue  # Try next selector if current one fails
            
            if latest_chapter:
                return {
                    'latest_chapter': f"第{latest_chapter}話",
                    'title': chapter_title,
                    'url': chapter_url or self.url
                }
            
            # If we couldn't find a chapter with selectors, look for common patterns in all links
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                text = link.get_text(strip=True)
                href = link.get('href')
                
                # Look for chapter-like patterns in all links
                chapter_match = re.search(r'(?:第|Ch|chap|Chapter|話|话)\s*(\d+(?:\.\d+)?)', text, re.IGNORECASE)
                if chapter_match:
                    chapter_num = chapter_match.group(1)
                    if latest_chapter is None or float(chapter_num) > float(latest_chapter):
                        latest_chapter = chapter_num
                        chapter_title = text
                        chapter_url = urljoin(self.url, href)
                        break
            
            if latest_chapter:
                return {
                    'latest_chapter': f"第{latest_chapter}話",
                    'title': chapter_title,
                    'url': chapter_url or self.url
                }
            
            print(f"[WARN] Could not parse latest chapter for {self.name}")
            return None
            
        except Exception as e:
            print(f"[ERROR] Exception occurred while parsing {self.name}: {str(e)}")
            return None
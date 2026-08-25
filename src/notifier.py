import os
import requests
from typing import List, Dict, Any
from datetime import datetime


class PushPlusNotifier:
    """Handles sending notifications via PushPlus"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv('PUSHPLUS_TOKEN')
        if not self.token:
            raise ValueError("PUSHPLUS_TOKEN is not configured. Please set the environment variable.")
        
        self.api_url = "http://www.pushplus.plus/send"
    
    def send_notification(self, updates: List[Dict[str, str]]) -> bool:
        """
        Send manga updates notification via PushPlus
        
        Args:
            updates: List of dictionaries containing manga update info
                    Each dict should have: 'name', 'chapter', 'url'
        
        Returns:
            True if notification sent successfully, False otherwise
        """
        if not updates:
            print("[INFO] No updates to send, skipping notification")
            return True
        
        # Format message content
        content_lines = ["【漫画更新通知】", ""]
        
        for update in updates:
            content_lines.append(f"📖 {update['name']}")
            content_lines.append(f"最新：{update['chapter']}")
            content_lines.append(f"链接：{update['url']}")
            content_lines.append("")
        
        content_lines.append(f"检测时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        content = "\n".join(content_lines)
        
        # Prepare payload
        payload = {
            "token": self.token,
            "title": f"漫画更新 ({len(updates)}部)",
            "content": content,
            "template": "markdown"
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print(f"[INFO] PushPlus notification sent successfully ({len(updates)} updates)")
                    return True
                else:
                    print(f"[ERROR] PushPlus API error: {result.get('msg', 'Unknown error')}")
                    return False
            else:
                print(f"[ERROR] PushPlus HTTP error: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to send PushPlus notification: {e}")
            return False
        except Exception as e:
            print(f"[ERROR] Unexpected error sending PushPlus notification: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test PushPlus connection with a test message"""
        try:
            payload = {
                "token": self.token,
                "title": "PushPlus Test",
                "content": f"PushPlus connection test successful!\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "template": "markdown"
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print("[INFO] PushPlus test notification sent successfully")
                    return True
                else:
                    print(f"[ERROR] PushPlus test failed: {result.get('msg', 'Unknown error')}")
                    return False
            else:
                print(f"[ERROR] PushPlus test HTTP error: {response.status_code}")
                return False
        except Exception as e:
            print(f"[ERROR] PushPlus test failed with exception: {e}")
            return False
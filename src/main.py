#!/usr/bin/env python3
"""
Manga Update Monitor
Automatically checks manga websites for new chapters and notifies via PushPlus
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Any

from .config import load_manga_config
from .state import StateManager
from .monitor import MangaMonitor
from .notifier import PushPlusNotifier


def main():
    parser = argparse.ArgumentParser(description='Manga Update Monitor')
    parser.add_argument('--config', default='config/manga.json', help='Path to manga config file')
    parser.add_argument('--state', default='data/state.json', help='Path to state file')
    parser.add_argument('--test-push', action='store_true', help='Test PushPlus connection only')
    parser.add_argument('--dry-run', action='store_true', help='Run checks without sending notifications or saving state')
    
    args = parser.parse_args()
    
    print("[INFO] Starting manga monitor...")
    
    # Load manga configuration
    try:
        manga_config = load_manga_config(args.config)
        print(f"[INFO] Loaded {len(manga_config)} manga configurations")
    except FileNotFoundError:
        print(f"[ERROR] Config file not found: {args.config}")
        print("[INFO] Creating example config file...")
        
        # Create example config
        example_config = [
            {
                "name": "Example Manga 1",
                "url": "https://example.com/manga1",
                "site": "example",
                "parser": "default",
                "enabled": True
            },
            {
                "name": "Example Manga 2",
                "url": "https://example.com/manga2",
                "site": "example",
                "parser": "default",
                "enabled": True
            }
        ]
        
        os.makedirs(os.path.dirname(args.config), exist_ok=True)
        with open(args.config, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] Example config created at {args.config}")
        print("[INFO] Please update the URLs with actual manga websites")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return 1
    
    # Filter enabled manga
    enabled_manga = [m for m in manga_config if m.get('enabled', True)]
    print(f"[INFO] {len(enabled_manga)} manga enabled for checking")
    
    if args.test_push:
        # Test PushPlus connection only
        print("[INFO] Testing PushPlus connection...")
        try:
            notifier = PushPlusNotifier()
            success = notifier.test_connection()
            return 0 if success else 1
        except ValueError as e:
            print(f"[ERROR] {e}")
            return 1
    
    # Initialize state manager
    state_manager = StateManager(args.state)
    
    # Initialize monitor
    monitor = MangaMonitor(enabled_manga, state_manager)
    
    # Run manga check
    updates = monitor.run_check()
    
    if updates:
        print(f"[INFO] {len(updates)} manga updates detected")
        
        if args.dry_run:
            print("[DRY_RUN] Would send notification:")
            for update in updates:
                print(f"  - {update['name']}: {update['current']} (was {update['previous']})")
        else:
            # Send notification via PushPlus
            try:
                notifier = PushPlusNotifier()
                success = notifier.send_notification([
                    {
                        'name': u['name'],
                        'chapter': u['current'],
                        'url': u['url']
                    } for u in updates
                ])
                
                if not success:
                    print("[ERROR] Failed to send notification")
                    return 1
                    
            except ValueError as e:
                print(f"[ERROR] {e}")
                return 1
            
            # Save state after successful notification
            if not state_manager.save_state():
                print("[ERROR] Failed to save state")
                return 1
    else:
        print("[INFO] No updates detected")
        
        if not args.dry_run:
            # Still save state to update last checked times
            if not state_manager.save_state():
                print("[ERROR] Failed to save state")
                return 1
    
    print("[INFO] Manga monitor completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
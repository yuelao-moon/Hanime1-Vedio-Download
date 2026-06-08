#!/usr/bin/env python3
"""Test watch-later functionality"""

import asyncio
import aiohttp
import json
from pathlib import Path

API_BASE = "http://127.0.0.1:1800"

async def test_watch_later():
    async with aiohttp.ClientSession() as session:
        # 1. Check login status
        print("\n[1] Checking login status...")
        resp = await session.get(f"{API_BASE}/api/auth/me")
        auth = await resp.json()
        print(f"    Logged in: {auth.get('loggedIn')}, User: {auth.get('username')}")

        if not auth.get("loggedIn"):
            print("    NOT logged in - cannot test")
            return

        user_id = auth.get("userId")
        print(f"    User ID: {user_id}")

        # 2. Try to get videos from search or browse
        print("\n[2] Attempting to get video list...")

        # Try search endpoint
        search_params = {"query": "", "page": 1}
        resp = await session.get(f"{API_BASE}/api/search", params=search_params)
        search_data = await resp.json()
        videos = search_data.get("items", [])
        print(f"    Search returned {len(videos)} videos")

        if not videos:
            print("    ERROR: No videos found!")
            # List cache info
            print("\n[DEBUG] Checking backend logs...")
            return

        # Choose first video
        video = videos[0]
        video_url = video.get("url")
        video_id = video.get("videoId") or (video_url.split("v=")[-1] if video_url else "")
        print(f"    Selected video: {video.get('title')}")
        print(f"    URL: {video_url}")
        print(f"    ID: {video_id}")

        if not video_url or not video_id:
            print("    ERROR: Missing video URL or ID")
            return

        # 3. Call watch-later API
        print(f"\n[3] Calling /api/video/watch-later (ADD)...")
        payload = {
            "videoId": video_id,
            "pageUrl": video_url,
            "isChecked": True
        }
        print(f"    Payload: videoId={video_id}, pageUrl={video_url}, isChecked=True")

        resp = await session.post(f"{API_BASE}/api/video/watch-later", json=payload)
        result_text = await resp.text()
        print(f"    Status: {resp.status}")
        print(f"    Response (first 200 chars): {result_text[:200]}")

        if resp.status != 200:
            print(f"    ERROR: API returned {resp.status}")
            print(f"    Full response: {result_text}")
            return

        # 4. Check watchLater section
        print(f"\n[4] Getting /api/profile/section/watchLater...")
        resp = await session.get(f"{API_BASE}/api/profile/section/watchLater?page=1")
        section_data = await resp.json()
        items = section_data.get("items", [])
        print(f"    Found {len(items)} videos in watchLater")

        # Check if our video is there
        found = False
        for item in items:
            item_id = item.get("videoId")
            item_url = item.get("url")
            item_title = item.get("title", "")
            if item_id == video_id or item_url == video_url:
                print(f"    SUCCESS! Found video: {item_title} (ID: {item_id})")
                found = True
                break

        if not found:
            print(f"    NOT FOUND! Video {video_id} not in watchLater")
            if items:
                print(f"    Current watchLater items:")
                for i, item in enumerate(items[:3]):
                    print(f"      {i+1}. {item.get('title')} (ID: {item.get('videoId')})")

        # 5. Try to remove and add again
        if found:
            print(f"\n[5] Testing REMOVE (isChecked=False)...")
            resp = await session.post(f"{API_BASE}/api/video/watch-later", json={
                **payload,
                "isChecked": False
            })
            print(f"    Status: {resp.status}")

            # Check again
            resp = await session.get(f"{API_BASE}/api/profile/section/watchLater?page=1")
            section_data = await resp.json()
            items = section_data.get("items", [])
            found_after_remove = any(
                item.get("videoId") == video_id or item.get("url") == video_url
                for item in items
            )
            if found_after_remove:
                print(f"    Still found after remove - REMOVE FAILED")
            else:
                print(f"    Successfully removed!")

if __name__ == "__main__":
    asyncio.run(test_watch_later())

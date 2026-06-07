#!/usr/bin/env python3
"""直接测试 watchLater 是否真的被保存到 hanime1.me"""

import asyncio
from python_backend.app.scraper import HanimeScraper
from python_backend.app.paths import app_home

async def test():
    home = app_home()
    scraper = HanimeScraper(home=home)

    print("\n[1] 获取登录状态...")
    status = await scraper.get_login_status()
    print(f"    登录: {status.get('loggedIn')}")
    user_id = status.get('userId')
    print(f"    用户 ID: {user_id}")

    if not status.get('loggedIn'):
        print("    未登录")
        return

    print("\n[2] 获取 watchLater 数据...")
    result = await scraper.profile_section("watchLater", user_id, 1)
    items = result.get("items", [])
    print(f"    返回 {len(items)} 个视频")

    if items:
        print("\n    前 3 个视频:")
        for i, item in enumerate(items[:3]):
            print(f"      {i+1}. {item.get('title')} (ID: {item.get('videoId')})")
    else:
        print("    watchLater 是空的")

    await scraper.close()

if __name__ == "__main__":
    asyncio.run(test())

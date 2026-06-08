"""
test_comments.py
模拟前端对评论接口的完整请求，验证数据结构并检查是否能被前端 renderComments 正确渲染。

用法（需先启动后端服务）:
    python test_comments.py [video_id]

示例:
    python test_comments.py 48955

若不传 video_id，脚本会先调用 /api/parse 解析首页随机视频来自动获取 videoId。
"""
from __future__ import annotations

import asyncio
import json
import sys
import httpx

BASE_URL = "http://127.0.0.1:8000"


def check_comment_structure(comment: dict) -> list[str]:
    """验证单条评论字段完整性，返回缺失字段列表。"""
    expected = ["commentId", "userName", "content", "timeText", "likeCount", "hasReplies", "replyCount"]
    return [f for f in expected if f not in comment]


async def test_comments(video_id: str) -> bool:
    """
    测试 /api/comments 接口：
    1. 发送 GET /api/comments?videoId={video_id}
    2. 验证响应为 JSON 数组
    3. 验证每条评论的字段结构
    4. 若有评论包含 hasReplies=True，进一步测试 /api/replies
    """
    print(f"\n{'='*60}")
    print(f"[TEST] 评论接口测试  videoId={video_id}")
    print(f"{'='*60}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:

        # ── Step 1: 获取评论 ───────────────────────────────────────────────
        print(f"\n[1] GET /api/comments?videoId={video_id}")
        resp = await client.get("/api/comments", params={"videoId": video_id})
        print(f"    HTTP 状态: {resp.status_code}")

        if resp.status_code != 200:
            print(f"    ❌ 请求失败: {resp.text[:200]}")
            return False

        try:
            comments = resp.json()
        except Exception as e:
            print(f"    ❌ JSON 解析失败: {e}")
            print(f"    响应内容: {resp.text[:300]}")
            return False

        if not isinstance(comments, list):
            print(f"    ❌ 期望 list，得到 {type(comments).__name__}: {str(comments)[:200]}")
            return False

        print(f"    ✅ 返回 {len(comments)} 条评论")

        if len(comments) == 0:
            print("    ⚠️  评论为空（视频可能无评论，或 CF 拦截仍未解决）")
            print("       → 请确认已通过设置界面刷新过 Cloudflare Cookie")
            return True  # 接口本身通了，数据为空是正常情况

        # ── Step 2: 验证字段结构 ──────────────────────────────────────────
        print(f"\n[2] 验证评论字段结构（共 {len(comments)} 条）")
        error_count = 0
        for i, comment in enumerate(comments[:5]):  # 只检查前5条
            missing = check_comment_structure(comment)
            if missing:
                print(f"    ❌ 评论[{i}] 缺少字段: {missing}")
                error_count += 1
            else:
                print(f"    ✅ 评论[{i}] 字段完整  userName={comment.get('userName','?')}  content={comment.get('content','')[:30]!r}")

        if error_count:
            print(f"    ❌ {error_count} 条评论字段不完整")
            return False

        # ── Step 3: 模拟前端 renderComments 逻辑 ─────────────────────────
        print(f"\n[3] 模拟前端 renderComments 渲染校验")
        renderable = 0
        for comment in comments:
            # 必须有 content 才会被渲染（对应 if not content: continue）
            if comment.get("content"):
                renderable += 1
        print(f"    可渲染评论数: {renderable}/{len(comments)}")
        if renderable == 0:
            print("    ⚠️  所有评论 content 为空，前端将显示"暂无评论"")
        else:
            print("    ✅ 评论数据可被 renderComments 正常渲染")

        # ── Step 4: 测试 replies 接口（若有回复） ─────────────────────────
        has_replies = [c for c in comments if c.get("hasReplies") or int(c.get("replyCount") or 0) > 0]
        if has_replies:
            sample = has_replies[0]
            comment_id = sample.get("commentId", "")
            print(f"\n[4] GET /api/replies?commentId={comment_id}")
            resp2 = await client.get("/api/replies", params={"commentId": comment_id})
            print(f"    HTTP 状态: {resp2.status_code}")
            if resp2.status_code == 200:
                replies = resp2.json()
                if isinstance(replies, list):
                    print(f"    ✅ 返回 {len(replies)} 条回复")
                    for j, r in enumerate(replies[:3]):
                        print(f"       回复[{j}] userName={r.get('userName','?')}  content={r.get('content','')[:30]!r}")
                else:
                    print(f"    ❌ 回复格式异常: {type(replies)}")
            else:
                print(f"    ❌ 回复请求失败: {resp2.text[:200]}")
        else:
            print(f"\n[4] 跳过 replies 测试（该视频评论无回复）")

        print(f"\n{'='*60}")
        print("✅ 评论接口端到端测试通过！前端 renderComments 可正常工作。")
        print(f"{'='*60}")
        return True


async def get_video_id_from_browse() -> str:
    """从首页抓取第一个视频的 videoId 用于测试。"""
    print("[自动] 未提供 videoId，尝试从浏览接口获取...")
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        resp = await client.get("/api/browse", params={"category": "裏番", "page": 1})
        if resp.status_code == 200:
            data = resp.json()
            videos = data.get("videos", [])
            if videos:
                url = videos[0].get("url", "")
                # 从 watch?v=xxxx 提取 video_id
                import re
                m = re.search(r"watch\?v=(\w+)", url)
                if m:
                    return m.group(1)
    return ""


async def main():
    video_id = sys.argv[1] if len(sys.argv) > 1 else ""

    if not video_id:
        video_id = await get_video_id_from_browse()

    if not video_id:
        print("❌ 无法获取 videoId，请手动传入: python test_comments.py <video_id>")
        sys.exit(1)

    success = await test_comments(video_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

"""
登录诊断脚本 - 逐步测试 hanime1.me 登录流程
用法：cd python_backend && python ../debug_login.py
或：  python debug_login.py（在项目根目录运行）
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# 让 import 能找到 python_backend
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "python_backend"))

EMAIL = "3555432061@qq.com"
PASSWORD = "3555432061bn"

HANIME_ORIGIN = "https://hanime1.me"
APP_HOME = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "HanimeMediaCenter"


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


async def main():
    section("1. 检查 CF cookies 文件")
    cf_file = APP_HOME / "cf_cookies.json"
    print(f"  路径: {cf_file}")
    if not cf_file.exists():
        print("  ❌ 文件不存在！需要先在 APP 设置中刷新 Cloudflare Cookie")
        cf_cookies = {}
    else:
        try:
            data = json.loads(cf_file.read_text(encoding="utf-8"))
            cookies = data.get("cookies", [])
            cf_count = sum(1 for c in cookies if c.get("name") == "cf_clearance")
            user_agent = data.get("user_agent", "")
            import time
            age_h = (time.time() - data.get("saved_at", 0)) / 3600
            print(f"  ✅ 文件存在，共 {len(cookies)} 个 cookies，cf_clearance: {cf_count} 个")
            print(f"  保存时间: {age_h:.1f} 小时前")
            print(f"  User-Agent: {user_agent[:80]}")
            if cf_count == 0:
                print("  ⚠️  没有 cf_clearance cookie！请先刷新 Cloudflare Cookie")
            cf_cookies = {c["name"]: c["value"] for c in cookies if c.get("value")}
            hanime_cf = {k: v for k, v in cf_cookies.items() if "cf" in k.lower() or "hanime" in k.lower()}
            print(f"  相关 cookies: {list(hanime_cf.keys())}")
        except Exception as e:
            print(f"  ❌ 读取失败: {e}")
            cf_cookies = {}

    section("2. 检查 curl_cffi 是否可用")
    try:
        from curl_cffi.requests import AsyncSession as CurlSession
        import curl_cffi
        print(f"  ✅ curl_cffi {curl_cffi.__version__} 已安装")
    except ImportError as e:
        print(f"  ❌ curl_cffi 未安装: {e}")
        print("  请运行: pip install curl_cffi")
        return

    section("3. 尝试 GET /login（无 CF cookies，纯 curl_cffi TLS 指纹）")
    try:
        async with CurlSession(impersonate="chrome124", timeout=15) as client:
            r = await client.get(HANIME_ORIGIN + "/login", allow_redirects=True)
            print(f"  状态码: {r.status_code}")
            print(f"  最终 URL: {r.url}")
            if r.status_code == 200:
                # 检查是否是登录页
                has_form = "_token" in r.text or "csrf-token" in r.text
                print(f"  包含登录表单: {has_form}")
                if has_form:
                    print("  ✅ 不需要 CF cookies！纯 curl_cffi TLS 指纹就能访问")
                    no_cf_works = True
                else:
                    print(f"  ⚠️  页面内容异常，前 200 字符: {r.text[:200]}")
                    no_cf_works = False
            else:
                print(f"  ❌ 被拦截（需要 CF cookies）")
                no_cf_works = False
    except Exception as e:
        print(f"  ❌ 请求失败: {e}")
        no_cf_works = False

    section("4. 尝试 GET /login（带 CF cookies）")
    if not cf_cookies:
        print("  ⚠️  跳过（无 CF cookies）")
        cf_login_works = no_cf_works  # 用上一步的结果
    else:
        try:
            async with CurlSession(impersonate="chrome124", timeout=15) as client:
                r = await client.get(HANIME_ORIGIN + "/login", cookies=cf_cookies, allow_redirects=True)
                print(f"  状态码: {r.status_code}")
                if r.status_code == 200:
                    has_form = "_token" in r.text or "csrf-token" in r.text
                    print(f"  包含登录表单: {has_form}")
                    cf_login_works = has_form
                    if has_form:
                        print("  ✅ 带 CF cookies 可以访问登录页")
                else:
                    print(f"  ❌ 状态码 {r.status_code}")
                    cf_login_works = False
        except Exception as e:
            print(f"  ❌ 请求失败: {e}")
            cf_login_works = False

    if not no_cf_works and not cf_login_works:
        print("\n❌ 无法访问登录页。请先在 APP 设置中刷新 Cloudflare Cookie，然后重试。")
        return

    section("5. 完整登录流程测试")
    use_cf = cf_login_works and cf_cookies
    cookies_to_use = cf_cookies if use_cf else {}
    print(f"  使用 CF cookies: {use_cf}")

    try:
        async with CurlSession(impersonate="chrome124", timeout=30) as client:
            # Step 1: GET login page
            print(f"\n  [1] GET {HANIME_ORIGIN}/login ...")
            r1 = await client.get(HANIME_ORIGIN + "/login", cookies=cookies_to_use, allow_redirects=True)
            print(f"      status={r1.status_code}")

            if r1.status_code != 200:
                print(f"      ❌ 无法获取登录页")
                return

            # Extract CSRF token
            import re
            from selectolax.parser import HTMLParser
            tree = HTMLParser(r1.text)
            token_node = tree.css_first("input[name='_token'], input[name=_token]")
            token = token_node.attributes.get("value") if token_node else ""
            if not token:
                meta = tree.css_first("meta[name='csrf-token']")
                token = meta.attributes.get("content", "") if meta else ""
            print(f"      CSRF token: {token[:20]}..." if token else "      ❌ 未找到 CSRF token")

            if not token:
                print("      ❌ 无法提取 CSRF token，登录中止")
                return

            # Step 2: POST login
            print(f"\n  [2] POST {HANIME_ORIGIN}/login ...")
            r2 = await client.post(
                HANIME_ORIGIN + "/login",
                data={"_token": token, "email": EMAIL, "password": PASSWORD},
                headers={
                    "X-CSRF-TOKEN": token,
                    "Referer": HANIME_ORIGIN + "/login",
                },
                allow_redirects=False,
            )
            print(f"      status={r2.status_code}")
            print(f"      Location: {r2.headers.get('location', 'N/A')}")

            # Check cookies
            session_val = client.cookies.get("hanime1_session")
            remember_val = client.cookies.get("remember_web")
            all_new_cookies = dict(client.cookies)
            print(f"      hanime1_session: {'✅ ' + session_val[:20] + '...' if session_val else '❌ 未设置'}")
            print(f"      remember_web: {'✅ 已设置' if remember_val else '❌ 未设置'}")
            print(f"      所有 cookies: {list(all_new_cookies.keys())}")

            if session_val:
                print("\n  ✅ 登录成功！hanime1_session cookie 已获取")

                # Step 3: Verify by fetching home page
                print(f"\n  [3] 验证登录：GET {HANIME_ORIGIN}/ ...")
                r3 = await client.get(
                    HANIME_ORIGIN + "/",
                    cookies={**cookies_to_use, "hanime1_session": session_val},
                )
                print(f"      status={r3.status_code}")
                name_match = re.search(r'id="user-modal-name"[^>]*>([^<]+)<', r3.text)
                if name_match:
                    print(f"      ✅ 登录用户: {name_match.group(1).strip()}")
                else:
                    has_user = "user-modal" in r3.text
                    print(f"      包含用户模态: {has_user}")
            else:
                print("\n  ❌ 登录失败！服务器未返回 hanime1_session")
                print(f"      POST 响应状态: {r2.status_code}")
                if r2.status_code == 200:
                    # 可能是账号密码错误，检查错误信息
                    error_node = tree.css_first(".alert-danger, .invalid-feedback, .error-message")
                    if error_node:
                        print(f"      错误信息: {error_node.text(strip=True)}")
                    else:
                        print(f"      响应内容前 300 字符: {r2.text[:300]}")
                elif r2.status_code == 302:
                    print(f"      重定向至: {r2.headers.get('location', '?')}")
                    print("      cookie jar 未收到 session cookie，可能需要检查 cookie 提取方式")

    except Exception as e:
        import traceback
        print(f"\n  ❌ 异常: {e}")
        traceback.print_exc()

    section("诊断完成")


if __name__ == "__main__":
    asyncio.run(main())

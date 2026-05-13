"""
경기도 정적 정책의 모든 URL이 접근 가능한지 검증
"""
import re
import sys
import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))

from crawler.sources.gyeonggi import _GG_STATIC_POLICIES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}
TIMEOUT = 10


def check_url(url: str) -> tuple[bool, int | str]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        return resp.status_code < 400, resp.status_code
    except requests.exceptions.SSLError:
        return False, "SSL Error"
    except requests.exceptions.ConnectionError:
        return False, "Connection Error"
    except Exception as e:
        return False, str(e)


def test_static_policy_links():
    urls: set[str] = set()
    for p in _GG_STATIC_POLICIES:
        if p.source_url:
            urls.add(p.source_url)
        if p.application_url:
            urls.add(p.application_url)

    print(f"\n검증할 URL: {len(urls)}개\n")
    failed = []
    for url in sorted(urls):
        ok, status = check_url(url)
        mark = "✅" if ok else "❌"
        print(f"  {mark} [{status}] {url}")
        if not ok:
            failed.append((url, status))

    if failed:
        print(f"\n❌ 실패한 링크 {len(failed)}개:")
        for url, status in failed:
            print(f"  - {url}  ({status})")
        assert False, f"접속 불가 URL {len(failed)}개 발견"
    else:
        print(f"\n✅ 모든 {len(urls)}개 링크 정상")


if __name__ == "__main__":
    test_static_policy_links()

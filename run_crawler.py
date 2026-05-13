"""
청년 정책 크롤러 실행 스크립트
사용법: python run_crawler.py [--source all|youth|housing|banks]
"""
import argparse
import sys
from datetime import datetime

from crawler.storage import init_db, bulk_upsert, get_stats
from crawler.sources.housing_fund import crawl_housing_fund
from crawler.sources.banks import crawl_banks
from crawler.sources.youth_portal import crawl_youth_portal


def run(source: str = "all"):
    print(f"\n{'='*50}")
    print(f"  청년 정책 크롤러 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  대상: {source}")
    print(f"{'='*50}\n")

    init_db()
    total_collected = 0

    if source in ("all", "housing"):
        print("[1/3] 주택도시기금 크롤링...")
        policies = crawl_housing_fund()
        bulk_upsert(policies)
        total_collected += len(policies)
        print(f"      -> {len(policies)}건 수집 완료\n")

    if source in ("all", "banks"):
        print("[2/3] 시중은행 대출 상품 크롤링...")
        policies = crawl_banks()
        bulk_upsert(policies)
        total_collected += len(policies)
        print(f"      -> {len(policies)}건 수집 완료\n")

    if source in ("all", "youth"):
        print("[3/3] 청년정책포털 크롤링...")
        policies = list(crawl_youth_portal(max_pages=20))
        bulk_upsert(policies)
        total_collected += len(policies)
        print(f"      -> {len(policies)}건 수집 완료\n")

    print(f"{'='*50}")
    print(f"  전체 수집 완료: {total_collected}건")

    stats = get_stats()
    print(f"\n[DB 현황]")
    print(f"  총 정책 수: {stats['total']}건")
    print(f"  유형별:")
    for ptype, cnt in stats["by_type"].items():
        print(f"    - {ptype}: {cnt}건")
    print(f"  출처별:")
    for src, cnt in stats["by_source"].items():
        print(f"    - {src}: {cnt}건")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="청년 정책 크롤러")
    parser.add_argument(
        "--source",
        choices=["all", "youth", "housing", "banks"],
        default="all",
        help="크롤링 대상 (기본값: all)",
    )
    args = parser.parse_args()
    run(args.source)

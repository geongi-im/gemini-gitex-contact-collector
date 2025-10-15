#!/usr/bin/env python3
"""
GITEX 참가 업체 연락처 정보 수집 스크립트
CSV에서 업체 정보를 읽어 Computer Use Agent로 연락처 정보를 수집합니다.
"""

import pandas as pd
import os
from computer_use_gemini import ComputerUseAgent
from pathlib import Path
import time

def process_exhibitors(input_csv: str = "output/gitex_exhibitors.csv",
                       output_csv: str = "output/gitex_exhibitors_detail.csv",
                       test_limit: int = 5,
                       start_index: int = 0):
    """
    업체 정보를 처리하여 연락처 정보를 수집합니다.

    Args:
        input_csv: 입력 CSV 파일 경로
        output_csv: 출력 CSV 파일 경로
        test_limit: 테스트용 처리 개수 제한 (None이면 전체 처리)
        start_index: 시작할 업체 인덱스 (0부터 시작)
    """
    # CSV 읽기
    print(f"📂 {input_csv} 파일을 읽는 중...")
    df = pd.read_csv(input_csv)
    print(f"✅ 총 {len(df)}개 업체 데이터 로드 완료")

    # website 컬럼이 있고 값이 비어있지 않은 행 필터링
    df_with_website = df[df['website'].notna() & (df['website'].str.strip() != '')]
    print(f"🌐 Website가 있는 업체: {len(df_with_website)}개")

    # 시작 인덱스 적용
    if start_index > 0:
        df_with_website = df_with_website.iloc[start_index:]
        print(f"🔢 시작 인덱스: {start_index} (총 {len(df_with_website)}개 업체 처리 예정)")

    # 테스트 제한 적용
    if test_limit:
        df_with_website = df_with_website.head(test_limit)
        print(f"🧪 테스트 모드: {test_limit}개 업체만 처리합니다.")

    # 기존 CSV 파일이 있으면 읽기, 없으면 새로 생성
    if os.path.exists(output_csv):
        result_df = pd.read_csv(output_csv)
        results = result_df.to_dict('records')
        print(f"📂 기존 결과 파일 발견: {len(results)}개 업체 데이터 로드")
    else:
        results = []
        # 헤더만 있는 CSV 생성
        pd.DataFrame(columns=['company_name', 'website', 'contact_email', 'contact_call']).to_csv(
            output_csv, index=False, encoding='utf-8-sig'
        )
        print(f"📂 새로운 결과 파일 생성: {output_csv}")

    # Computer Use Agent 초기화 (headless=True로 백그라운드 실행)
    print("\n🤖 Computer Use Agent를 초기화합니다...\n")

    # 이미 처리된 업체 확인
    processed_companies = {r['company_name'] for r in results} if results else set()

    # 각 업체 처리
    success_count = 0
    fail_count = 0

    for idx, row in df_with_website.iterrows():
        company_name = row['company_name']
        website = row['website']

        # 이미 처리된 업체는 스킵
        if company_name in processed_companies:
            print(f"⏭️ 스킵 (이미 처리됨): {company_name}")
            continue

        print(f"\n{'='*80}")
        print(f"[{len(results)+1}/{len(df_with_website)}] 처리 중: {company_name}")
        print(f"Website: {website}")
        print(f"{'='*80}\n")

        try:
            # Agent 생성 (매번 새로 생성)
            agent = ComputerUseAgent(headless=True)

            # 작업 실행
            task = f"{website} 페이지에서 회사 파트너십 문의 이메일로 판단할 수 있는 이메일(contact_email) 1개와 대표 전화번호(contact_call) 1개를 찾아서 json 형식으로 주세요"

            result = agent.run_task(task=task, url=website, max_turns=15)

            if result and isinstance(result, dict):
                contact_email = result.get('contact_email', '')
                contact_call = result.get('contact_call', '')

                new_record = {
                    'company_name': company_name,
                    'website': website,
                    'contact_email': contact_email,
                    'contact_call': contact_call
                }

                results.append(new_record)

                print(f"✅ 성공: {company_name}")
                print(f"   이메일: {contact_email}")
                print(f"   전화번호: {contact_call}")
                success_count += 1
            else:
                print(f"⚠️ JSON 추출 실패: {company_name}")
                new_record = {
                    'company_name': company_name,
                    'website': website,
                    'contact_email': '',
                    'contact_call': ''
                }
                results.append(new_record)
                fail_count += 1

            # 즉시 CSV에 추가 (append mode)
            pd.DataFrame([new_record]).to_csv(
                output_csv,
                mode='a',
                header=False,
                index=False,
                encoding='utf-8-sig'
            )
            print(f"💾 {output_csv}에 저장 완료")

            # 요청 간 대기 (API 제한 고려)
            time.sleep(2)

        except Exception as e:
            print(f"❌ 오류 발생 ({company_name}): {str(e)}")
            new_record = {
                'company_name': company_name,
                'website': website,
                'contact_email': '',
                'contact_call': ''
            }
            results.append(new_record)
            fail_count += 1

            # 오류 발생 시에도 CSV에 저장
            pd.DataFrame([new_record]).to_csv(
                output_csv,
                mode='a',
                header=False,
                index=False,
                encoding='utf-8-sig'
            )
            print(f"💾 {output_csv}에 저장 완료 (오류)")

    # 최종 통계
    print(f"\n{'='*80}")
    print(f"✅ 모든 처리 완료! 결과: {output_csv}")
    print(f"📊 처리 통계:")
    print(f"   - 총 처리: {len(results)}개 업체")
    print(f"   - 성공: {success_count}개")
    print(f"   - 실패: {fail_count}개")
    print(f"{'='*80}\n")

    return pd.DataFrame(results)

if __name__ == "__main__":
    import sys

    # 명령줄 인자로 start_index와 test_limit 받기
    # 사용 예: python process_exhibitors.py 10 5  (10번 인덱스부터 5개)
    start_idx = 100
    test_lim = 500

    print(f"📍 시작 인덱스: {start_idx}, 처리 개수: {test_lim}\n")
    process_exhibitors(start_index=start_idx, test_limit=test_lim)

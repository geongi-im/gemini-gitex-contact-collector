# GITEX 전시회 참가업체 연락처 수집 프로젝트

Google Gemini 2.5 Computer Use 모델을 활용하여 GITEX 전시회 참가업체의 연락처 정보를 자동으로 수집하는 프로젝트입니다.

## 프로젝트 개요

이 프로젝트는 GITEX 전시회 참가업체 목록을 크롤링하고, 각 업체의 공식 웹사이트에서 연락처 정보(이메일, 전화번호)를 자동으로 추출하는 시스템입니다.

## 주요 기능

- **GITEX 전시회 참가업체 크롤링**: GITEX 공식 사이트에서 참가업체 목록 자동 수집
- **웹사이트 정보 수집**: 각 업체의 공식 웹사이트 URL 추출
- **AI 기반 연락처 추출**: Gemini 2.5 Computer Use 모델을 사용한 자동 연락처 정보 수집
- **데이터 저장**: CSV 형태로 구조화된 데이터 저장

## 프로젝트 구조

```
request_gitex/
├── computer_use_gemini.py          # Gemini 2.5 Computer Use 에이전트
├── get_gitex_company.py           # GITEX 참가업체 크롤링 스크립트
├── process_exhibitors.py          # 연락처 정보 수집 메인 스크립트
├── requirements.txt               # 프로젝트 의존성
└── output/                        # 결과 데이터 저장 폴더
    ├── gitex_exhibitors.csv       # 참가업체 기본 정보
    └── gitex_exhibitors_detail*.csv # 연락처 정보 수집 결과
```

## 설치 및 설정

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

```bash
playwright install-deps chrome
playwright install chrome
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 Gemini API 키를 설정합니다:

```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## 사용 방법

### 1. GITEX 참가업체 목록 수집

```bash
python get_gitex_company.py
```

이 스크립트는 GITEX 공식 사이트에서 참가업체 정보를 크롤링하여 `output/gitex_exhibitors.csv`에 저장합니다.

### 2. 연락처 정보 자동 수집

```bash
python process_exhibitors.py
```

이 스크립트는 수집된 업체 정보를 바탕으로 각 업체의 웹사이트에서 연락처 정보를 자동으로 추출합니다.

## 주요 컴포넌트

### ComputerUseAgent 클래스

- **기능**: Gemini 2.5 Computer Use 모델을 사용한 브라우저 자동화
- **지원 액션**: 클릭, 텍스트 입력, 페이지 이동, 스크롤 등
- **결과 반환**: JSON 형태로 구조화된 데이터 반환

### 데이터 수집 프로세스

1. **1단계**: GITEX 사이트에서 참가업체 기본 정보 수집
2. **2단계**: 각 업체의 공식 웹사이트 URL 추출
3. **3단계**: AI 에이전트를 사용한 연락처 정보 자동 추출
4. **4단계**: 결과를 CSV 파일로 저장

## 출력 데이터 형식

### 참가업체 기본 정보 (gitex_exhibitors.csv)
- `company_name`: 회사명
- `stand_no`: 부스 번호
- `description`: 회사 설명
- `profile_url`: GITEX 프로필 URL
- `website`: 공식 웹사이트

### 연락처 정보 (gitex_exhibitors_detail*.csv)
- `company_name`: 회사명
- `website`: 공식 웹사이트
- `contact_email`: 연락처 이메일
- `contact_call`: 연락처 전화번호

## 기술 스택

- **Python 3.x**: 메인 프로그래밍 언어
- **Google Gemini 2.5**: AI 모델 (Computer Use 기능)
- **Playwright**: 브라우저 자동화
- **BeautifulSoup**: 웹 스크래핑
- **Pandas**: 데이터 처리
- **Requests**: HTTP 요청 처리

## 주의사항

- Gemini API 사용량에 따른 비용이 발생할 수 있습니다
- 웹사이트 접근 제한을 고려하여 적절한 대기 시간을 설정했습니다
- 대량 데이터 처리 시 시간이 오래 걸릴 수 있습니다

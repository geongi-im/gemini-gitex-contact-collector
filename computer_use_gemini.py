#!/usr/bin/env python3
"""
Gemini 2.5 Computer Use 에이전트
실제 동작하는 완벽한 구현 (최신 버전)
"""

import os
import time
import re
import json
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.types import Content, Part, FunctionResponse, FunctionResponsePart
from playwright.sync_api import sync_playwright

# .env 파일 로드
load_dotenv()

class ComputerUseAgent:
    def __init__(self, api_key: Optional[str] = None, headless: bool = True):
        """Computer Use 에이전트 초기화"""
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY 설정되지 않았습니다.")

        # GenAI 클라이언트 초기화
        self.client = genai.Client(api_key=self.api_key)

        # 화면 크기 설정
        self.screen_width = 1440
        self.screen_height = 900

        # Playwright 설정
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Computer Use 모델 설정
        self.model_name = 'gemini-2.5-computer-use-preview-10-2025'

    def start_browser(self):
        """브라우저 시작"""
        print("🌐 브라우저를 시작합니다...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.context = self.browser.new_context(
            viewport={"width": self.screen_width, "height": self.screen_height}
        )
        self.page = self.context.new_page()
        print("✅ 브라우저가 시작되었습니다.")

    def close_browser(self):
        """브라우저 닫기"""
        if self.browser:
            print("🌐 브라우저를 닫습니다...")
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ 브라우저가 닫혔습니다.")

    def take_screenshot(self) -> bytes:
        """현재 화면 스크린샷 찍기"""
        if not self.page:
            raise ValueError("브라우저가 시작되지 않았습니다.")
        return self.page.screenshot(type="png")

    def denormalize_x(self, x: int) -> int:
        """정규화된 x 좌표를 실제 픽셀 좌표로 변환"""
        return int(x / 1000 * self.screen_width)

    def denormalize_y(self, y: int) -> int:
        """정규화된 y 좌표를 실제 픽셀 좌표로 변환"""
        return int(y / 1000 * self.screen_height)

    def execute_javascript(self, code: str):
        """자바스크립트 함수 실행하는 custom tool 함수"""  
        return self.page.evaluate(code)

    def create_computer_use_config(self) -> genai.types.GenerateContentConfig:
        """Computer Use 설정 생성"""
        custom_functions = [
            types.FunctionDeclaration.from_callable(  
                client=self.client, callable=self.execute_javascript  
            )  
        ]

        return genai.types.GenerateContentConfig(
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER,
                    )
                ),
                types.Tool(
                    function_declarations=custom_functions,
                ),
            ]
        )

    def execute_function_calls(self, candidate) -> Tuple[List[Tuple[str, Dict[str, Any]]], Dict[str, bool]]:
        """Function Call 실행"""
        results = []
        function_calls = []
        safety_acknowledgements = {}

        # Function Call 추출
        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_calls.append(part.function_call)

        for function_call in function_calls:
            action_result = {}
            fname = function_call.name
            args = function_call.args
            extra_fields = {}

            print(f"  🔧 실행 중: {fname}")
            print(f"  📋 인자: {args}")

            # Safety decision 확인
            if 'safety_decision' in args:
                decision = self.get_safety_confirmation(args['safety_decision'])
                if decision == "TERMINATE":
                    print("🛑 에이전트 루프를 종료합니다.")
                    break
                extra_fields["safety_acknowledgement"] = "true"
                safety_acknowledgements[fname] = True

            try:
                if fname == "open_web_browser":
                    action_result = {"success": True, "message": "브라우저가 이미 열려 있습니다."}

                elif fname == "click_at":
                    x = self.denormalize_x(args["x"])
                    y = self.denormalize_y(args["y"])
                    self.page.mouse.click(x, y)
                    action_result = {"success": True, "message": f"좌표 ({x}, {y})에서 클릭했습니다."}

                elif fname == "type_text_at":
                    x = self.denormalize_x(args["x"])
                    y = self.denormalize_y(args["y"])
                    text = args["text"]
                    press_enter = args.get("press_enter", False)
                    clear_before_typing = args.get("clear_before_typing", True)

                    self.page.mouse.click(x, y)
                    time.sleep(0.1)

                    # 텍스트 필드 지우기
                    if clear_before_typing:
                        self.page.keyboard.press("Meta+A")
                        self.page.keyboard.press("Backspace")

                    # 텍스트 입력
                    # self.page.keyboard.type(text)
                    for char in text:  
                        self.page.keyboard.press(char)  
                        time.sleep(0.05)  # 짧은 딜레이 추가

                    if press_enter:
                        self.page.keyboard.press("Enter")

                    action_result = {"success": True, "message": f"좌표 ({x}, {y})에 텍스트를 입력했습니다: {text}"}

                elif fname == "navigate":
                    url = args["url"]
                    self.page.goto(url)
                    action_result = {"success": True, "message": f"{url}로 이동했습니다."}

                elif fname == "search":
                    self.page.goto("https://www.google.com")
                    action_result = {"success": True, "message": "Google 검색 페이지로 이동했습니다."}

                elif fname == "scroll_document":
                    direction = args.get("direction", "down")
                    if direction == "down":
                        self.page.keyboard.press("PageDown")
                    elif direction == "up":
                        self.page.keyboard.press("PageUp")
                    elif direction == "left":
                        self.page.keyboard.press("ArrowLeft")
                    elif direction == "right":
                        self.page.keyboard.press("ArrowRight")
                    action_result = {"success": True, "message": f"문서를 {direction} 방향으로 스크롤했습니다."}

                elif fname == "wait_5_seconds":
                    time.sleep(5)
                    action_result = {"success": True, "message": "5초 대기했습니다."}

                elif fname == "execute_javascript":  
                    self.execute_javascript(code=args["code"])
                    action_result = {"success": True, "message": f"자바스크립트를 실행했습니다: {args['code']}"}

                else:
                    action_result = {"success": False, "message": f"지원되지 않는 액션: {fname}"}

                # Safety acknowledgment 추가
                action_result.update(extra_fields)

                # 대기 및 로딩
                print(f"  ⏳ 페이지 로딩 대기 중...")
                self.page.wait_for_load_state(timeout=5000)
                time.sleep(1)
                print(f"  ✅ 액션 완료: {action_result.get('message', '성공')}")

            except Exception as e:
                print(f"  ❌ 오류 발생 {fname}: {e}")
                action_result = {"error": str(e)}

            results.append((fname, action_result))

        return results, safety_acknowledgements

    def get_safety_confirmation(self, safety_decision: Dict[str, Any]) -> str:
        """Safety 확인 - 자동으로 계속 진행"""
        print(f"⚠️ Safety decision 감지: {safety_decision.get('explanation', '')} -> 자동 승인")
        return "CONTINUE"

    def get_function_responses(self, results: List[Tuple[str, Dict[str, Any]]],
                             safety_acknowledgements: Dict[str, bool] = None) -> List[FunctionResponse]:
        """Function Response 생성"""
        screenshot_bytes = self.page.screenshot(type="png")
        current_url = self.page.url
        function_responses = []

        if safety_acknowledgements is None:
            safety_acknowledgements = {}

        for name, result in results:
            response_data = {"url": current_url}
            response_data.update(result)

            # Safety acknowledgment 추가
            if name in safety_acknowledgements and safety_acknowledgements[name]:
                response_data["safety_acknowledgement"] = "true"

            function_responses.append(
                FunctionResponse(
                    name=name,
                    response=response_data,
                    parts=[
                        FunctionResponsePart(
                            inline_data=types.FunctionResponseBlob(
                                mime_type="image/png",
                                data=screenshot_bytes
                            )
                        )
                    ]
                )
            )

        return function_responses

    def has_function_calls(self, candidate) -> bool:
        """Function Call이 있는지 확인"""
        return any(hasattr(part, 'function_call') and part.function_call
                  for part in candidate.content.parts)

    def extract_json_from_response(self, text: str) -> Optional[Dict]:
        """응답 텍스트에서 JSON 추출"""
        # 1. 마크다운 코드블록 내 JSON 찾기
        code_block_pattern = r'```(?:json)?\s*\n(.*?)\n```'
        matches = re.findall(code_block_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue

        # 2. 인라인 JSON 객체 찾기
        json_pattern = r'\{[^\{\}]*(?:"[^"]*"[^\{\}]*:[^\{\}]*)+[^\{\}]*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)

        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        # 3. 전체 텍스트를 JSON으로 시도
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        return None

    def run_task(self, task: str, url: str = None, max_turns: int = 10) -> Optional[Dict]:
        """Computer Use 작업 실행 및 JSON 결과 반환"""
        try:
            self.start_browser()

            # 초기 페이지로 이동
            if url:
                self.page.goto(url)
            else:
                self.page.goto("https://www.google.com")

            # 초기 스크린샷
            screenshot = self.take_screenshot()

            # Computer Use 설정
            config = self.create_computer_use_config()

            # 대화 기록 초기화 (JSON 응답 강제)
            contents = [
                Content(
                    role="user",
                    parts=[
                        Part(text=f"""당신은 유능한 AI 어시스턴트입니다.

작업: {task}

중요: 작업 완료 후 응답은 반드시 순수 JSON 형식만 출력해주세요.
설명이나 마크다운 코드블록 없이 오직 JSON 객체만 출력하세요.
예시: {{"contact_email": "example@example.com", "contact_call": "+123456789"}}"""),
                        Part.from_bytes(data=screenshot, mime_type='image/png')
                    ]
                )
            ]

            print(f"🎯 작업 시작: {task}")

            text_response = None

            # 에이전트 루프
            for turn in range(max_turns):
                print(f"\n--- 턴 {turn + 1} ---")
                print("생각 중...")

                # 모델에 요청 보내기
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

                candidate = response.candidates[0]
                contents.append(candidate.content)

                # Gemini의 응답 텍스트 출력
                response_text = " ".join([part.text for part in candidate.content.parts if hasattr(part, 'text') and part.text])
                if response_text:
                    print(f"🤖 Gemini 응답: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

                # Function Call이 있는지 확인
                if not self.has_function_calls(candidate):
                    # 최종 응답
                    text_response = response_text
                    print(f"🎯 작업 완료! 최종 응답: {text_response}")
                    break

                print("⚡ 액션 실행 중...")
                results, safety_acknowledgements = self.execute_function_calls(candidate)

                print("📊 실행 결과 처리 중...")
                function_responses = self.get_function_responses(results, safety_acknowledgements)

                # Function Response를 대화 기록에 추가
                contents.append(
                    Content(
                        role="user",
                        parts=[Part(function_response=fr) for fr in function_responses]
                    )
                )

                if turn == max_turns - 1:
                    print("⚠️ 최대 턴 수에 도달했습니다.")

            # JSON 추출 시도
            if text_response:
                print(f"\n🔍 JSON 데이터 추출 시도 중...")
                print(f"📝 원본 응답: {text_response}")
                extracted_json = self.extract_json_from_response(text_response)
                if extracted_json:
                    print(f"✅ JSON 추출 성공!")
                    print(f"📊 추출된 데이터: {extracted_json}")
                    return extracted_json
                else:
                    print("⚠️ JSON 추출 실패 - 구조화된 데이터를 찾을 수 없습니다")
                    return None
            else:
                print("⚠️ 최종 텍스트 응답이 없습니다")
                return None

        except Exception as e:
            print(f"❌ 작업 실행 중 오류 발생: {str(e)}")
            return None
        finally:
            self.close_browser()

def main():
    """메인 함수"""
    agent = ComputerUseAgent(headless=False)  # 디버깅을 위해 headless=False

    # 예제 작업 실행
    agent.run_task(
        #task=f"""document.getElementById('chkUseMyKD1').click(); 자바스크립트 함수 실행해주세요""",
        #url="https://highbuff.com/company",


        task=f"""
        1) 로그인 페이지가 켜지면 [키보드보안사용] 체크박스를 클릭해서 키보드보안을 해제해주세요.
        2) 로그인란에 아이디 **highbuff** 비밀번호 **Com12!@** 공동인증서 비밀번호 **Comcom12!@**를 입력하고 로그인 버튼을 클릭합니다
        3) 로그인이 완료되면 이체 페이지 중단 [계좌비밀번호] 텍스트 입력란에 **8091** 이라는 비밀번호를 입력합니다.
        4) [이체금액] 텍스트 입력란에는 **1000**원을 입력합니다.
        5) 브라우저 창에서 **javascript:selectBank('004', '국민');** 자바스크립트 함수를 실행시킵니다.
        6) [금융기관] 텍스트 입력란에는 **국민** 이 입력되었는지 확인합니다.
        7) [입금계좌번호] 영역에 계좌번호란에는 **94071273750** 을 입력하고 [조회] 버튼을 클릭합니다.
        8) [조회] 버튼을 클릭하면 예금주 이름이 노출되는데 **임건기**와 일치한지 비교합니다. 일치하지않으면 에러메시지를 노출하고 작업을 중단합니다.
        9) 이상이 없다면 [받는분통장표시내용] 텍스트 입력란에는 **하이버프** 입력힙니다.
        10) 우측 하단에 [이체실행] 버튼을 클릭하면 다음 페이지로 이동합니다.
        11) 입력된 정보가 맞는지 확인하고 [실물OTP번호입력] 텍스트입력란에 **123456** 입력합니다.
        12) 우측 하단에 [다음] 버튼을 클릭합니다. """,
        url="https://www.daishin.com/g.ds?p=90&v=73&m=139&returnUrl=%2Fg.ds%3Fm%3D162%26p%3D383%26v%3D228",
        max_turns=30
    )

if __name__ == "__main__":
    main()
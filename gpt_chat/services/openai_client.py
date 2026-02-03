import os 
from typing import List, Dict

from openai import OpenAI
# 
def generate_assistant_reply(
    *,
    messages: List[Dict[str, str]],
    model: str,
) -> str:
    """
    OpenAI Responses API를 호출하여 assistant 응답 텍스트를 반환합니다.

    Parameters:
        messages (List[Dict[str, str]]): 대화 메시지 목록
            예시:
                [
                    {"role": "developer", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "안녕하세요."},
                ]
        model (str): 사용할 모델명
            예시: "gpt-4o-mini", "gpt-5.2"

    Returns:
        str: assistant가 생성한 응답 텍스트
    """

    # OpenAI SDK는 기본적으로 OPENAI_API_KEY 환경변수를 읽습니다. :contentReference[oaicite:8]{index=8}
    # 다만, 명시적으로 주입해 두면 설정 누락을 더 빨리 발견할 수 있습니다.
    api_key = os.getenv("OPENAI_API_KEY")
    # 체크
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 환경변수에 없습니다. .env 로딩을 확인해 주세요.")

    client = OpenAI(api_key=api_key)

    # Responses API 호출
    # - input 에 문자열을 넣을 수도 있고,
    # - role/content 형태의 메시지 배열을 넣어 대화 형태로도 요청할 수 있습니다. :contentReference[oaicite:9]{index=9}
    response = client.responses.create(
        model=model,
        input=messages,
    )

    # Python 예시에서도 output_text로 결과 텍스트를 얻습니다. :contentReference[oaicite:10]{index=10}
    return response.output_text
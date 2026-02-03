import json

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .models import Conversation, Message
from .services.openai_client import generate_assistant_reply



def _get_or_create_conversation(request) -> Conversation:
    """
    세션 기반으로 Conversation 을 찾거나 새로 만듭니다. 
    - 로그인/유저 모델이 없는 상태에서도 최소 기능을 수행할 수 있도록 함.
    """
    
    # 대화 ID 
    conversation_id = request.session.get("get_chat_conversation_id")
    print("conversation_id:", conversation_id)
    # 만약 위 값이 없는경우 
    
    if conversation_id:
        # 대화 ID호츌        
        conversation = Conversation.objects.filter(id=conversation_id).first()

        print("conversation:", conversation)
        # 만약 이 값이 있다면 반환
        if conversation:
            return conversation
        
    
    conversation = Conversation.objects.create()
    print("new conversation:", conversation)
    
    # 세션 저장
    request.session["get_chat_conversation_id"] = conversation.id
    print( "set session conversation id:", conversation.id)

    return conversation

def _build_prompt_messages(conversation: Conversation):
    
    prompt_messages = []

    prompt_messages.append(
        {
            "role": "developer",
            "content": "You are a helpful assistant. Answer in polite Korean.",
        }
    )

    # 과거 대화 컨텍스트를 모델에 전달
    # 너무 길어지는 경우 비용 및 딜레이 문제가 발생하므로 최근 N 개로 제한하는 전략을 사용.
    recent_messages = conversation.messages.all().order_by("-created_at")[:20]
    print("현재 recent_messages:", len(list(recent_messages)))
    
    recent_messages = reversed(list(recent_messages))  # 시간순 정렬

    # 위 내용을 하나씩 꺼내 추가 
    for msg in recent_messages:
        prompt_messages.append(
            {
                "role": msg.role,
                "content": msg.content,
            }
        )

    return prompt_messages


@require_http_methods(['GET'])
def chat_page(request):
    """
    채팅 페이지 렌더링 영역
    """
    conversation = _get_or_create_conversation(request=request)
    messages = conversation.messages.all()  # 미리 로드 

    return render(
        request,
        "gpt_chat/chat.html",
        {
            "messages": messages,
        },
    )

@require_http_methods(['POST'])
def send_message_api(request):
    """
    프론트엔드에서 user 메시지를 POST 로 보내면, 
    1) DB 저장
    2) OpenAI API 호출
    3) assistant 응답 DB 저장
    4) JSON 으로 반환
    """

    conversation = _get_or_create_conversation(request=request)

    # Json 바디 파싱
    try:
        payload = json.loads(request.body.decode("utf-8"))
    
    except json.JSONDecodeError:
        return HttpResponseBadRequest("잘못된 JSON 형식입니다.")
    
    user_text = payload.get("message", "")
    user_text = user_text.strip()

    if not user_text:
        return HttpResponseBadRequest("Message 값이 비어 있습니다.")
    
    # 1) user 메시지 저장 DB
    Message.objects.create(
        conversation=conversation,
        role="user",
        content=user_text,
    )

    # 2) 프롬프트 구성 + OpenAI 호출 
    prompt_messages = _build_prompt_messages(conversation=conversation)

    try:
        assistant_text = generate_assistant_reply(
            messages=prompt_messages,
            model=settings.OPENAI_MODEL,
        )
    except Exception as e:
        # 운영에서는 로깅에러 코드 설계 필수
        return JsonResponse({"error": f"OpenAI API 호출 중 오류가 발생했습니다: {str(e)}"}, status=500)
    
    # 3) assistant 응답 저장 DB
    Message.objects.create(
        conversation=conversation,
        role="assistant",
        content=assistant_text,
    )

    return JsonResponse(
        {
            "reply": assistant_text,
        }
    )

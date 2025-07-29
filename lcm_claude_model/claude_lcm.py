from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(
    model="claude-3-haiku-20240307",  # ✅ 또는 "claude-3-opus-20240229" 등
    temperature=0.5,
    anthropic_api_key="dd"  # 교수님 키
)

response = llm.invoke("컴활 1급 자주 나오는 개념 알려줘")
print(response)

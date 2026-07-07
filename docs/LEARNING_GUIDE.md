# 학습 가이드 (LEARNING_GUIDE)

RAG · AI Agent · LLM Wiki · ROS2를 **어떻게 익힐지**와 추천 자료. 각 주제마다 "핵심 개념 → 손으로 해볼 것 → 흔한 함정"으로 정리했습니다.

> 원칙: **개념 → 최소 코드 → 이 프로젝트에 적용.** 튜토리얼만 보지 말고 [로드맵](ROADMAP.md)의 각 Phase에 바로 연결해서 만들면서 익히세요.

---

## 0. 공통 기반 — LLM API (Claude)

이 프로젝트의 두뇌는 **Claude API**입니다. 세 기술 전부 여기 위에 올라갑니다.

- **모델 선택**: 기본 `claude-sonnet-5`(속도/비용 균형), 어려운 추론·에이전트 루프는 `claude-opus-4-8`. 최신 SDK와 최신 모델을 쓰세요.
- **기본 호출** (Python):
  ```python
  import anthropic
  client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
  resp = client.messages.create(
      model="claude-sonnet-5",
      max_tokens=1024,
      messages=[{"role": "user", "content": "안녕"}],
  )
  print(next(b.text for b in resp.content if b.type == "text"))
  ```
- **꼭 알아둘 최신 사항** (예전 자료와 다름):
  - **thinking(추론)**: `thinking={"type": "adaptive"}` 사용. 예전의 `budget_tokens` 방식은 최신 모델에서 400 에러.
  - **effort**: `output_config={"effort": "high"}` 로 추론 깊이·토큰 조절 (`low`/`medium`/`high`/`xhigh`/`max`).
  - **키 관리**: `ANTHROPIC_API_KEY` 환경변수, `.gitignore`에 등록, 절대 커밋 금지.
- **자료**: [Claude API 문서](https://docs.claude.com) · [모델 개요](https://platform.claude.com/docs/en/about-claude/models/overview)

---

## 1. RAG (Retrieval-Augmented Generation) 🟦

### 핵심 개념
LLM에 **외부 지식을 검색해서 근거로 주입**하는 기법. "문서를 조각내(청킹) → 벡터로 임베딩 → 질문과 유사한 조각을 검색 → 그 조각을 프롬프트에 넣어 답변 + 출처 인용."

핵심 용어: **청킹(chunking)**, **임베딩(embedding)**, **벡터DB**, **검색(retrieval)**, **리랭킹(reranking)**, **citation(출처)**, **할루시네이션 억제**.

### 손으로 해볼 것 (Phase 1과 직결)
1. 문서(ROS2 md, 스펙 텍스트) 몇 개를 500~1000토큰 단위로 청킹
2. 임베딩 → 벡터DB 저장 (**Chroma**로 시작 → 나중에 pgvector)
3. 질문 → 상위 k개 검색 → 프롬프트 조립 → Claude 답변
4. **출처 강제**: 시스템 프롬프트에 *"제공된 문서에 근거해서만 답하고, 없으면 '모른다'고 하라. 각 주장에 출처 번호를 달아라"*
5. Claude의 **문서 인용 기능**(`citations: {enabled: True}`)도 실험 — 텍스트 문서를 `document` 블록으로 넣으면 인용을 구조적으로 반환

### 흔한 함정
- **청크가 너무 큼/작음** → 검색 정확도 하락. 크기·오버랩을 바꿔가며 비교.
- **출처 강제를 안 함** → LLM이 그럴듯하게 지어냄(할루시네이션). 프롬프트로 반드시 억제.
- **평가 없이 진행** → "잘 되는 것 같다"에 그침. Phase 5에서 질문-정답-근거 셋으로 정확도 측정.

### 자료
- Anthropic [Contextual Retrieval 가이드](https://www.anthropic.com/news/contextual-retrieval)
- 벡터DB: [Chroma](https://www.trychroma.com/) (입문), [pgvector](https://github.com/pgvector/pgvector) (실전 Postgres)

---

## 2. AI Agent (도구 사용) 🟩

### 핵심 개념
LLM이 **도구(함수)를 호출**하며 여러 단계를 스스로 판단·실행하는 것. "질문 → LLM이 도구 선택 → 도구 실행 → 결과를 다시 LLM에 → 반복 → 최종 답변" (ReAct 루프).

핵심 용어: **tool calling(도구 호출)**, **에이전트 루프**, **멀티스텝 추론**, **도구 설계**.

### 손으로 해볼 것 (Phase 2와 직결)
1. **도구 정의** — 이름·설명·입력 스키마. 설명은 *언제 쓰는지*까지 구체적으로:
   ```python
   @beta_tool
   def navigate_to(x: float, y: float, theta: float) -> str:
       """로봇을 목표 좌표로 이동시킨다. 사용자가 특정 위치로 가라고 할 때 호출.

       Args:
           x: 목표 x좌표 (미터)
           y: 목표 y좌표 (미터)
           theta: 목표 방향 (라디안)
       """
       return send_nav_goal(x, y, theta)
   ```
2. **Tool Runner로 루프 자동화** (직접 while 루프 짜기 전에 SDK 헬퍼부터):
   ```python
   runner = client.beta.messages.tool_runner(
       model="claude-opus-4-8", max_tokens=4096,
       tools=[navigate_to, get_robot_state, query_knowledge],
       messages=[{"role": "user", "content": "창고 구역으로 가"}],
   )
   for message in runner:
       print(message)
   ```
3. **수동 루프**도 한 번 짜보기 — `stop_reason == "tool_use"`를 확인하고 `tool_result`를 돌려주는 흐름을 이해해야 ROS2 노드로 옮길 수 있음
4. **RAG를 도구로 노출** — `query_knowledge`가 Layer 1을 호출 → 에이전트가 지식이 필요할 때 스스로 검색 (레이어 합성)

### 흔한 함정
- **도구를 너무 많이/모호하게** → LLM이 혼란. 초점 있는 소수의 도구 + 명확한 설명.
- **부작용 있는 도구에 확인 없음** → 로봇을 움직이는 도구는 **안전 검증**을 반드시 사이에 (이 프로젝트의 C++ Executor가 그 역할).
- **병렬 도구 결과를 나눠서 반환** → 한 assistant 턴의 여러 `tool_use`는 **한 user 메시지**에 모든 `tool_result`를 담아 반환.

### 자료
- Anthropic [Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [Tool use 개요](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)

---

## 3. LLM Wiki (자동 문서화) 🟨

### 핵심 개념
LLM으로 **구조화된 지식 문서를 생성·갱신**하는 것. 이 프로젝트에선 ROS2 시스템을 introspection 해서 노드별 위키를 자동 생성.

핵심 용어: **structured generation(구조화 생성)**, **grounding(근거화)**, **요약**, **크로스링크**.

### 손으로 해볼 것 (Phase 3과 직결)
1. **입력 수집** — `ros2 node/topic/service list`, 그래프 관계, 소스 주석
2. **구조화 출력** — 정해진 스키마(개요/토픽/서비스/파라미터/관계)로 생성. Claude의 structured outputs(`output_config.format`)로 JSON 스키마를 강제하면 파싱이 안정적
3. **grounding 강제** — *"주어진 introspection 데이터에 있는 것만 서술하라. 없는 토픽/노드를 지어내지 마라"*
4. **mermaid 다이어그램** 자동 생성 + 페이지 간 크로스링크

### 흔한 함정
- **grounding 안 함** → 없는 토픽을 지어냄. RAG와 같은 원칙 — 사실에만 근거.
- **한 번에 다 생성** → 큰 시스템은 노드 단위로 나눠 생성하고 합치기.
- **갱신 전략 없음** → 시스템이 바뀌면 재생성되도록 CLI/서비스로 트리거화.

### 자료
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — 반복 생성 시 비용 절감

---

## 4. ROS2 (로봇 미들웨어) 🤖

### 핵심 개념
로봇 소프트웨어를 **노드(node)** 단위로 나누고 **토픽/서비스/액션**으로 통신하는 프레임워크. 이 프로젝트의 뼈대이자 당신 채용 타겟의 핵심.

핵심 개념: **노드**, **토픽**(pub/sub), **서비스**(요청/응답), **액션**(장시간 작업+피드백), **파라미터**, **tf2**(좌표변환), **QoS/DDS**, **colcon**(빌드), **launch**.

### 손으로 해볼 것 (Phase 0~4에 걸쳐)
1. **Phase 0**: rclpy(Python) publisher + rclcpp(C++) subscriber가 통신 → 커스텀 인터페이스 패키지
2. **Phase 1**: rclpy로 **서비스 서버** (RAG를 `~/query` 서비스로 래핑)
3. **Phase 2**: rclcpp로 **액션 서버** (`ExecuteCommand`) + tf2로 로봇 상태 읽기 + Safety Monitor
4. **Phase 4**: Gazebo + Nav2 위에서 실제 로봇 구동

### 언어 분리 (C++·Python 균형 — 채용 타겟)
- **C++ (rclcpp)**: 실시간·안전 중요 노드 — Executor, Safety Monitor, (선택) 커스텀 컨트롤러
- **Python (rclpy)**: AI 오케스트레이션·글루 — RAG, Agent 두뇌, Wiki
- 커스텀 인터페이스(`copilot_msgs`)를 양쪽에서 공유 → ROS2 인터페이스 설계 학습의 핵심

### 흔한 함정
- **환경 구축에서 막힘** → Docker 이미지로 시작하면 OS 의존성 문제 회피
- **QoS 불일치** → pub/sub의 QoS 프로파일이 안 맞으면 메시지가 안 옴. 초반에 자주 겪는 함정
- **tf 트리 디버깅** → `ros2 run tf2_tools view_frames`, RViz로 시각화
- **한 번에 시뮬까지** → Nav2가 버거우면 `cmd_vel` 직접 발행으로 단순화 → 나중에 Nav2

### 자료
- [ROS2 공식 튜토리얼](https://docs.ros.org/en/humble/Tutorials.html) — 반드시 처음부터
- [Nav2 문서](https://docs.nav2.org/) · [Gazebo](https://gazebosim.org/)
- 책/강의: "Programming Robots with ROS", 공식 rclcpp/rclpy 예제 리포

---

## 5. 통합 학습 순서 (요약)

```
LLM API 기초  →  RAG(로봇 없이)  →  Agent+도구  →  ROS2로 이식  →  Wiki  →  시뮬  →  평가
   (0)            (1)              (2)            (병행)         (3)      (4)     (5)
```

각 단계에서:
1. 위 개념을 읽고
2. 최소 예제를 손으로 돌려보고
3. [로드맵](ROADMAP.md)의 해당 Phase에 적용하고
4. 배운 점을 `docs/`에 기록 → **이 기록이 곧 당신의 학습 가이드이자 블로그·면접 소재**

막히면 범위를 줄이세요. 완벽한 한 방보다, 돌아가는 작은 조각을 자주 만드는 게 학습에 훨씬 빠릅니다.

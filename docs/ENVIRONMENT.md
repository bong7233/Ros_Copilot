# 실행 환경 가이드 (ENVIRONMENT)

> "이거 윈도우 전용이야? .exe 하나 나오는 거야, 웹앱이야?" 에 대한 답 + 실제 실행 방법.

---

## 1. 이 프로젝트는 무엇인가 (실행 형태)

**하나의 실행파일(.exe)도, 웹앱도 아닙니다.** ROS2 Copilot은 **여러 개의 노드(프로세스)가 DDS로 통신하는 분산 시스템**입니다.

```
copilot_rag (프로세스)  ─┐
copilot_executor (C++)   ├─ DDS로 서로 통신 ─ 하나의 "로봇 시스템"
copilot_safety_monitor   │
copilot_agent            │
Nav2 / Gazebo 노드들     ─┘
```

- **상호작용 방법**: 지금은 **CLI**(`ros2 run`, `ros2 service call`, `ros2 launch`) + **RViz/Gazebo GUI**.
- 여러 노드를 한 번에 띄우는 건 **launch 파일**(`copilot_bringup`)이 담당합니다.
- **웹앱으로 만들 수도 있어요(선택, Phase 6)**: `copilot_agent`의 `~/ask` 서비스를 감싸는 얇은 웹 계층(예: `rosbridge_suite` + FastAPI/React)을 얹으면 "채팅으로 로봇에 명령하는 웹 데모"가 됩니다. 이 레포가 원래 웹 프로젝트였으니 자연스러운 확장이에요. 코어(ROS2)는 그대로 두고 프론트만 추가하는 구조입니다.

---

## 2. 어떤 OS에서 도나

**윈도우 전용이 아니라, 오히려 리눅스가 메인입니다.** ROS2·Nav2·Gazebo는 **Ubuntu 우선**이에요.

| 방법 | 대상 | 비고 |
|---|---|---|
| **Ubuntu 22.04 네이티브** | 리눅스 사용자 | 가장 매끄러움. ROS2 Humble 설치 |
| **WSL2 (Ubuntu)** | 윈도우 사용자 | Windows 11 + WSLg면 GUI(Gazebo/RViz)도 됨 |
| **Docker** | 모든 OS | 이 레포에 이미지 제공 (`docker/`). GUI는 X 서버 설정 필요 |
| 네이티브 윈도우 ROS2 | 비추천 | 코어는 되지만 Nav2/Gazebo가 까다로움 |

> 지금 로컬 테스트가 안 되는 상황이라면 → **Docker**가 가장 쉽습니다. 아래 4번 참고.

---

## 3. 필요한 것

- **ROS2 Humble** (또는 Jazzy)
- **Phase 0~3**: `anthropic`, `chromadb` (pip) + `ANTHROPIC_API_KEY`
- **Phase 4(시뮬)**: `ros-humble-navigation2`, `ros-humble-nav2-bringup`, `ros-humble-turtlebot3-gazebo`, `TURTLEBOT3_MODEL` 환경변수

---

## 4. Docker로 실행 (로컬 ROS2 설치 없이)

레포 루트에서:

```bash
# 1. 이미지 빌드 (ROS2 Humble + Nav2 + TB3 + pip 의존성까지 포함)
docker build -f docker/Dockerfile -t robo-copilot .

# 2. 컨테이너 실행 (헤드리스)
ANTHROPIC_API_KEY=sk-ant-... ./docker/run.sh

# 컨테이너 안에서:
cd /ws/src/copilot_rag && python3 -m copilot_rag.ingest data
python3 -m copilot_rag.ask "costmap inflation이 뭐야?"
# 또는 전체 AI 노드:
ros2 launch copilot_bringup copilot.launch.py
```

**Gazebo GUI가 필요하면** (Phase 4 시뮬):
- 리눅스 호스트: `xhost +local:docker` 후 `./docker/run.sh gui`
- 윈도우: WSLg(Win11) 또는 VcXsrv 같은 X 서버 필요
- macOS: XQuartz 필요

GUI 없이 헤드리스로도 로직(RAG/Agent/Nav2)은 테스트할 수 있습니다.

---

## 5. Ubuntu 네이티브로 실행

```bash
# ROS2 Humble 설치는 공식 문서 참고: https://docs.ros.org/en/humble/Installation.html
cd ros2_copilot_ws
rosdep install --from-paths src --ignore-src -r -y   # ROS 의존성
pip install anthropic chromadb                        # AI 의존성
colcon build && source install/setup.bash
export ANTHROPIC_API_KEY=sk-ant-...
ros2 launch copilot_bringup copilot.launch.py
```

---

## 6. 정리 (면접에서 설명할 때)

- "단일 바이너리가 아니라 **ROS2 노드들의 분산 시스템**이고, launch로 오케스트레이션합니다."
- "**리눅스(Ubuntu) 기반**이며, 재현성을 위해 **Docker 이미지**로 패키징했습니다."
- "CLI로 조작하지만, `~/ask` 서비스를 감싸면 **웹 프론트엔드**도 붙일 수 있는 구조입니다."

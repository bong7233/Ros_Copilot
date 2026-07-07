# 실행 가이드 (HOW_TO_RUN) — 누구나 따라 하는 실행법

> **이 문서 하나만 따라 하면** 프로그래밍을 몰라도 이 프로젝트를 내 컴퓨터에서 실행하거나 웹앱으로 사용해볼 수 있습니다. 면접관에게 보여줄 때도 이 문서를 그대로 건네주면 됩니다.
>
> _최종 갱신: 2026-07-07 · 대상: Windows 11 / 리눅스 / macOS · 문서 버전 v1_

---

## 0. 30초 요약

- 이 프로젝트는 **"자연어로 로봇에게 말하면 알아듣고 움직이는 AI 시스템"** 입니다. (RAG·AI Agent·LLM Wiki 기술 사용)
- 실행하려면 **리눅스 환경**이 필요한데, **Windows 11은 새 PC 없이** 그 환경을 만들 수 있습니다.
- 가장 쉬운 길: **Docker Desktop 설치 → 명령 몇 개 → 브라우저에서 챗으로 로봇과 대화.**
- 필요한 것: ① Windows 11 PC, ② 인터넷, ③ Anthropic API 키(소액 유료), ④ 30분~1시간.

---

## 1. 먼저 알아둘 3가지 (아주 쉽게)

1. **이 프로젝트는 하나의 앱(.exe)이 아니라, 여러 프로그램이 협력하는 시스템**입니다. 그래서 "실행"은 여러 부품을 함께 켜는 것에 가깝습니다. 아래 명령들이 그걸 대신 해줍니다.
2. **리눅스에서 도는 소프트웨어**(ROS2)라서 리눅스 환경이 필요합니다. Windows 11에서는 **Docker**나 **WSL2**가 리눅스 환경을 대신 만들어 줍니다. (새 컴퓨터 불필요)
3. **로봇의 "두뇌"는 Claude AI**입니다. 그래서 **Anthropic API 키**가 필요합니다. (아래 3번에서 발급)

---

## 2. 두 가지 실행 경로 — 뭘 고를까?

| | 경로 A: Docker (추천, 쉬움) | 경로 B: WSL2 우분투 (완전판) |
|---|---|---|
| 난이도 | ⭐ 쉬움 | ⭐⭐⭐ 보통 |
| 할 수 있는 것 | **웹 챗 · RAG · 에이전트 · 평가** | 위 전부 **+ Gazebo 3D 로봇 시뮬레이션 화면** |
| 걸리는 시간 | 약 30분 (대부분 다운로드 대기) | 약 1~2시간 |
| 면접 데모용 | ✅ 웹 챗이 인상적이고 보여주기 쉬움 | ✅ 로봇 움직이는 영상까지 |

**추천 순서**: 먼저 **경로 A**로 웹 챗을 띄워 보세요. 그게 되면 여유 있을 때 **경로 B**로 시뮬레이션까지 도전하면 됩니다.

---

## 3. 공통 준비 — Anthropic API 키 발급

로봇의 두뇌가 쓸 열쇠입니다. (프로그래밍 지식 불필요)

1. 웹브라우저에서 **<https://console.anthropic.com>** 접속 → 가입/로그인.
2. 결제 수단 등록: 왼쪽 메뉴 **Billing** → 카드 등록 후 소액(예: $5) 충전.
   - 이 프로젝트를 테스트하는 정도면 보통 **$1 미만**만 씁니다. 걱정 안 해도 됩니다.
3. 왼쪽 메뉴 **API Keys** → **Create Key** → 이름 아무거나 → 생성.
4. 나온 키(`sk-ant-...`로 시작하는 긴 문자열)를 **복사해서 안전한 곳에 메모**하세요. 이 창을 닫으면 다시 못 봅니다.

> ⚠️ 이 키는 비밀번호와 같습니다. 누구에게도 주지 말고, 코드나 깃허브에 올리지 마세요. (이 프로젝트는 `.env`/환경변수로만 쓰도록 만들어져 있어 안전합니다.)

---

## 4. 경로 A — Docker로 웹앱 실행 (추천 시작점)

### 4-1. Docker Desktop 설치
1. **<https://www.docker.com/products/docker-desktop/>** 에서 **Docker Desktop for Windows** 다운로드 → 설치 → 재부팅.
2. 설치 중 "**Use WSL 2 based engine**" 옵션이 있으면 체크(기본값). Windows 11이면 자동으로 됩니다.
3. 설치 후 Docker Desktop을 실행해 두세요(고래 아이콘이 켜져 있어야 함).

### 4-2. 프로젝트 코드 내려받기
가장 쉬운 방법(깃 몰라도 됨):
1. 이 프로젝트의 GitHub 페이지에서 초록색 **Code** 버튼 → **Download ZIP**.
2. 다운로드한 ZIP을 압축 해제. 예: `C:\robo_market` 폴더가 되도록.

(깃을 쓸 줄 알면 `git clone`도 됩니다.)

### 4-3. 이미지 빌드 (한 번만, 시간이 좀 걸림)
1. 시작 메뉴에서 **PowerShell** 실행.
2. 프로젝트 폴더로 이동 (경로는 본인 것에 맞게):
   ```powershell
   cd C:\robo_market
   ```
3. 빌드 명령 (ROS2·Nav2 등 모두 담긴 리눅스 이미지를 만듭니다. **10~30분 소요, 수 GB 다운로드**):
   ```powershell
   docker build -f docker/Dockerfile -t robo-copilot .
   ```
   - 마지막에 에러 없이 프롬프트가 돌아오면 성공입니다.

### 4-4. 웹앱 실행 (거의 한 줄)
1. 3번에서 복사한 API 키를 넣어 실행 (PowerShell):
   ```powershell
   docker run -it --rm -p 8000:8000 -e ANTHROPIC_API_KEY="sk-ant-여기에-본인-키" robo-copilot bash /app/docker/web-demo.sh
   ```
2. 화면에 `[3/3] Starting the web server on http://localhost:8000` 이 뜨면 준비 완료.
3. 브라우저에서 **<http://localhost:8000>** 접속.
4. 채팅창에 이렇게 입력해 보세요:
   - `costmap inflation이 뭐야?` → 로봇이 문서를 검색해 **출처와 함께** 답합니다. (🟦 RAG)
   - `좌표 (2, 1)로 가줘` → 에이전트가 이동 명령을 실행합니다. (🟩 Agent)
   - `좌표 (100, 100)로 가` → **범위 밖이라 거부**하고 정직하게 알려줍니다. (안전장치)
5. 종료: PowerShell 창에서 **Ctrl + C**.

> 이 웹 화면이 면접관에게 보여주기 가장 좋은 데모입니다. "브라우저에서 로봇 AI와 대화하는 시스템"이 바로 보이니까요.

---

## 5. 경로 B — WSL2 + Ubuntu로 전체 실행 (Gazebo 시뮬 포함)

로봇이 3D 화면에서 실제로 돌아다니는 걸 보고 싶을 때. Windows 11의 **WSLg** 덕분에 별도 프로그램 없이 GUI가 뜹니다.

### 5-1. WSL2 + Ubuntu 설치
1. **PowerShell을 "관리자 권한으로"** 실행 (시작 메뉴에서 우클릭 → 관리자).
2. 설치 명령:
   ```powershell
   wsl --install
   ```
3. 재부팅. 재부팅 후 Ubuntu 창이 뜨면 **사용자 이름과 비밀번호**를 정합니다. (비번 입력 시 화면에 안 보이는 게 정상)
4. 확인:
   ```powershell
   wsl --version
   ```

### 5-2. Ubuntu 안에서 ROS2 설치
> 이제부터는 **Ubuntu 터미널**(검은 창)에 입력합니다. 아래는 공식 방법이며, 혹시 명령이 바뀌었으면 공식 페이지 <https://docs.ros.org/en/humble/Installation.html> 를 따르세요.

```bash
# 한글/UTF-8 설정
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ROS2 저장소 등록
sudo apt install -y software-properties-common curl
sudo add-apt-repository -y universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# ROS2 + 시뮬레이션 도구 설치
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-humble-desktop ros-dev-tools \
  ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-turtlebot3-gazebo
```

### 5-3. 프로젝트 받고 빌드
```bash
# 프로젝트 받기 (git 사용)
sudo apt install -y git python3-pip
cd ~
git clone <이-프로젝트의-GitHub-주소> robo_market
cd robo_market

# AI 라이브러리 설치
pip3 install -r requirements.txt

# ROS2 워크스페이스 빌드
source /opt/ros/humble/setup.bash
cd ros2_copilot_ws
colcon build
source install/setup.bash
```

### 5-4. 실행하기
매번 새 터미널을 열면 아래 두 줄을 먼저 실행하세요(환경 불러오기):
```bash
source /opt/ros/humble/setup.bash
source ~/robo_market/ros2_copilot_ws/install/setup.bash
export ANTHROPIC_API_KEY="sk-ant-본인-키"
export TURTLEBOT3_MODEL=burger
```

**(a) RAG만 먼저 확인** (가장 간단):
```bash
cd ~/robo_market/ros2_copilot_ws/src/copilot_rag
python3 -m copilot_rag.ingest data
python3 -m copilot_rag.ask "costmap inflation이 뭐야?"
```

**(b) AI 노드 전체 + 에이전트 대화**:
```bash
# 터미널 1
ros2 launch copilot_bringup copilot.launch.py
# 터미널 2 (위 환경 두 줄 실행 후)
ros2 run copilot_agent agent_cli "좌표 (2,1)로 가줘"
```

**(c) Gazebo 3D 시뮬레이션** (로봇이 화면에서 움직임):
```bash
ros2 launch copilot_bringup sim.launch.py
```
- Gazebo/RViz 창이 뜹니다(WSLg). 그다음 다른 터미널에서 `agent_cli`로 명령하면 로봇이 이동합니다.
- ⚠️ 시뮬은 맵/버전에 민감합니다. 창이 안 뜨거나 에러가 나면 [문제 해결](#7-자주-나는-문제--해결)과 `copilot_bringup/README.md`를 참고하세요.

**(d) 웹앱** (경로 A와 같은 화면):
```bash
pip3 install -r ~/robo_market/web/backend/requirements.txt
# (a)/(b)의 노드가 켜진 상태에서:
uvicorn server:app --app-dir ~/robo_market/web/backend --host 0.0.0.0 --port 8000
# 브라우저에서 http://localhost:8000
```

---

## 6. 실제로 써보기 — 면접 데모 대본 (3분)

1. **웹 챗 열기** → "브라우저에서 로봇 AI와 대화하는 시스템입니다."
2. `내 subscriber가 메시지를 못 받아. 뭘 확인해야 해?` 입력
   → "문서를 검색해 **출처와 함께** 답합니다. 이게 **RAG**입니다." (QoS 답변 나옴)
3. `좌표 (2,1)로 가줘` 입력
   → "에이전트가 스스로 판단해 **이동 도구를 호출**합니다. 이게 **AI Agent**입니다."
4. `좌표 (100,100)로 가` 입력
   → "범위 밖이라 **C++ 안전 계층이 거부**합니다. LLM이 틀려도 로봇은 안전합니다."
5. (여유되면) 시뮬 화면 or `ros2 run copilot_wiki generate --dry-run`
   → "실행 중인 시스템을 읽어 **문서를 자동 생성**합니다. 이게 **LLM Wiki**입니다."

한 줄 마무리: *"RAG·에이전트·Wiki 같은 최신 AI를 ROS2 로봇에 결합했고, C++/Python 모두 사용했으며, Docker로 어디서든 실행됩니다."*

---

## 7. 자주 나는 문제 & 해결

| 증상 | 해결 |
|---|---|
| `docker: command not found` | Docker Desktop이 실행 중인지 확인(고래 아이콘). 재부팅 후 다시. |
| 빌드가 매우 오래 걸림 | 정상입니다. ROS2 전체를 받습니다. 인터넷 속도에 따라 10~30분. |
| `ANTHROPIC_API_KEY` 관련 오류 / 답이 안 옴 | 키를 정확히 넣었는지, Anthropic Billing에 잔액이 있는지 확인. |
| 웹에서 "도구 unavailable"이라고 답함 | ROS2 노드가 안 켜진 것. Docker `web` 데모는 자동으로 켭니다. 수동 실행 시 `copilot.launch.py`를 먼저 켜세요. |
| RAG가 "찾지 못했습니다"만 답함 | 문서를 먼저 넣어야 함: `python3 -m copilot_rag.ingest data`. |
| subscriber가 메시지를 못 받음(직접 코딩 시) | QoS 불일치일 확률이 큼 — 이 프로젝트 문서 `ros2_qos.md` 참고. |
| Gazebo 창이 안 뜸(WSL2) | Windows 11인지 확인, `wsl --update` 실행, GPU 드라이버 최신화. |
| 포트 8000 사용 중 | 다른 프로그램이 쓰는 중. 명령의 `8000`을 `8080` 등으로 바꾸고 브라우저 주소도 맞추기. |

---

## 8. 아주 쉬운 용어 사전

- **터미널 / PowerShell / 셸**: 명령을 글자로 입력하는 검은 창.
- **명령(command)**: 컴퓨터에게 시키는 한 줄 글. 위 코드 블록을 그대로 복사-붙여넣기 하면 됩니다.
- **소스코드**: 프로그램을 이루는 글(파일). 이 프로젝트가 그 모음입니다.
- **빌드(build)**: 소스코드를 실제 실행 가능한 형태로 만드는 과정.
- **Docker / 컨테이너**: 프로그램과 그 실행 환경을 통째로 담은 상자. 어느 PC에서든 똑같이 실행됨.
- **WSL2**: 윈도우 안에서 진짜 리눅스를 돌리는 기능. WSLg는 그 리눅스의 화면(GUI)까지 보여줌.
- **ROS2**: 로봇 소프트웨어를 만드는 표준 틀. 이 프로젝트의 뼈대.
- **노드(node)**: ROS2에서 하나의 일을 맡은 작은 프로그램. 여러 노드가 모여 시스템이 됨.
- **API 키**: 외부 AI(Claude)를 쓰기 위한 비밀 열쇠.

---

## 9. 문서 갱신 이력

- **v1 (2026-07-07)**: 최초 작성. Windows 11(Docker/WSL2) + 리눅스 실행법, 웹 데모, 면접 대본, 문제 해결.

> 이 문서는 프로젝트가 발전하면 계속 갱신됩니다. 실행 중 막힌 부분이 있으면 알려주세요 — 그 내용을 이 문서의 [문제 해결](#7-자주-나는-문제--해결)에 추가하겠습니다.

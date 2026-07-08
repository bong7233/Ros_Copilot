# 윈도우 11 빠른 실행 (Docker) — 5단계

> 지금 쓰는 **Windows 11 데스크톱**에서 바로 실행하는 최단 경로입니다. 리눅스 PC 없이 브라우저에서 로봇 AI와 채팅할 수 있어요. (Gazebo 3D 시뮬레이션은 리눅스/WSL2가 필요하니 리눅스 PC가 오면 [실행 가이드](HOW_TO_RUN.md) 경로 B로 하세요.)
>
> 소요: 30분~1시간 (대부분 다운로드 대기) · 비용: Claude API 소액(테스트는 보통 $1 미만)

---

## 준비물 3가지
1. Windows 11 + 인터넷
2. **Docker Desktop** (아래 1단계)
3. **Anthropic API 키** (아래 2단계)

---

## 1단계 · Docker Desktop 설치
1. <https://www.docker.com/products/docker-desktop/> → **Download for Windows** → 설치 → **재부팅**.
2. Docker Desktop 실행 (오른쪽 아래 고래 아이콘이 켜져 있어야 함).
3. 만약 설치 중 "WSL2가 필요하다"는 안내가 나오면: **시작 → PowerShell을 관리자 권한으로 실행** → `wsl --install` 입력 → 재부팅 후 Docker Desktop 다시 실행.

## 2단계 · Claude API 키 발급
1. <https://console.anthropic.com> 가입/로그인.
2. **Billing** 메뉴 → 카드 등록 후 소액(예: $5) 충전.
3. **API Keys** → **Create Key** → 생성된 `sk-ant-...` 문자열을 **복사해서 메모**. (창 닫으면 다시 못 봄)

## 3단계 · 코드 내려받기
<https://github.com/bong7233/Ros_Copilot> → 초록색 **Code** 버튼 → **Download ZIP** → 압축 해제.
예: `C:\robo` 안에 풀어서 폴더가 `C:\robo\Ros_Copilot-main` 이 되게 합니다.

## 4단계 · 이미지 빌드 (한 번만, 10~30분)
1. 시작 메뉴에서 **PowerShell** 실행.
2. 압축 푼 폴더로 이동 (경로는 본인 것에 맞게, 폴더에 `docker` 와 `ros2_copilot_ws` 가 보여야 함):
   ```powershell
   cd C:\robo\Ros_Copilot-main
   ```
3. 빌드:
   ```powershell
   docker build -f docker/Dockerfile -t robo-copilot .
   ```
   에러 없이 프롬프트가 돌아오면 성공.

## 5단계 · 웹 챗 실행
1. `sk-ant-...` 부분을 본인 키로 바꿔서 실행:
   ```powershell
   docker run -it --rm -p 8000:8000 -e ANTHROPIC_API_KEY="sk-ant-여기에-본인-키" robo-copilot bash /app/docker/web-demo.sh
   ```
2. 화면에 `Starting the web server on http://localhost:8000` 이 뜨면 준비 완료.
3. 브라우저에서 **<http://localhost:8000>** 접속 → 채팅:
   - `costmap inflation이 뭐야?` → 🟦 문서를 검색해 **출처와 함께** 답
   - `좌표 (2, 1)로 가줘` → 🟩 에이전트가 이동 명령 실행 (🔧 도구 호출이 실시간 표시)
   - `좌표 (100, 100)로 가` → 범위 밖이라 **안전하게 거부**
4. **종료**: PowerShell 창에서 `Ctrl + C`.

---

## 문제 해결 (자주 나는 것만)
| 증상 | 해결 |
|---|---|
| `docker: command not found` / 응답 없음 | Docker Desktop이 실행 중인지(고래 아이콘) 확인, 필요시 재부팅 |
| 빌드가 오래 걸림 | 정상. ROS2 전체를 받습니다(수 GB). 인터넷 속도에 따라 다름 |
| 답이 안 오거나 키 오류 | 키를 정확히 넣었는지, Anthropic **Billing 잔액**이 있는지 확인 |
| `localhost:8000` 안 열림 | `-p 8000:8000` 을 빠뜨렸는지 확인. 5단계 명령을 그대로 복사 |
| 포트 8000 사용 중 | 명령의 `8000:8000` 을 `8080:8000` 으로 바꾸고 브라우저는 `localhost:8080` |

---

## 참고
- 이건 "웹 챗" 데모 경로입니다. **로봇이 3D로 움직이는 Gazebo 시뮬**은 리눅스 PC(또는 Windows 11 WSL2)가 필요 → [실행 가이드](HOW_TO_RUN.md) 경로 B.
- 실행하다 막히면 **PowerShell에 뜬 에러 메시지를 그대로 복사해서 알려주세요.** 바로 고쳐드립니다.

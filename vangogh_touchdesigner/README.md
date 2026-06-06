# 고흐풍 인터랙티브 비주얼 — TouchDesigner + RealSense D435

관람객의 깊이·동작을 RealSense D435로 읽어, **반 고흐 '별이 빛나는 밤'처럼
휘감기는 붓터치가 실시간으로 살아 움직이는** 비주얼을 만드는 프로젝트입니다.

`.toe` 파일은 바이너리라 여기엔 포함하지 않았고, 대신 그 안에 붙여넣을
**GLSL 셰이더 + Python + 노드별 조립 가이드**를 담았습니다. 아래 순서대로
TouchDesigner에서 노드를 연결하면 동작합니다.

---

## 0. 준비물

- TouchDesigner (무료 비상업 라이선스로 충분, 2022 이상 권장)
- Intel RealSense **D435** + USB 3.0 케이블
- Intel RealSense SDK 2.0 (`librealsense`) 설치 — TD의 RealSense TOP이 이걸 씀
- 이 폴더의 파일들

```
vangogh_touchdesigner/
├── README.md              ← 지금 이 문서
├── glsl/
│   ├── 00_motion.frag     ← 동작 감지 (프레임 차)
│   ├── 01_flowfield.frag  ← 흐름장 생성 (소용돌이 결)  ★핵심
│   ├── 02_advect.frag     ← 색을 흘려 붓터치 누적      ★핵심
│   ├── 03_kuwahara.frag   ← 유화 임파스토 질감
│   └── 04_palette.frag    ← 고흐 색조 그레이딩
├── python/
│   ├── make_palette.py    ← 팔레트 PNG 생성기 (numpy/pillow 필요)
│   └── params.py          ← 프리셋(starry_night/calm/storm) 일괄 적용
└── assets/
    └── vangogh_palette.png ← 이미 생성해 둔 팔레트 CLUT (바로 사용 가능)
```

---

## 1. 전체 신호 흐름

```
[RealSense TOP]
   ├─ Depth  ─────────────────────────────┐
   └─ Color ─┬─→ [GLSL: 00_motion] ─Motion─┤
             │        ↑(1프레임 지연)        │
             │                              ▼
             │                   [GLSL: 01_flowfield] ──Flow──┐
             │                                                 ▼
             └────────────→ Source 색 ───────────→ [GLSL: 02_advect] ←─Feedback─┐
                                                          │                       │
                                                          ├───────────────────────┘
                                                          ▼
                                              [GLSL: 03_kuwahara]
                                                          ▼
                              [Movie File In: 팔레트] ─→ [GLSL: 04_palette]
                                                          ▼
                                                  [Out TOP] → 프로젝터/화면
```

핵심 한 줄 요약: **RealSense는 "움직임의 힘"을 만들고(00·01), advect(02)가 그
힘을 따라 색을 흘려 붓 자국을 쌓고, kuwahara·palette(03·04)가 고흐 유화로 마감.**

---

## 2. 노드별 설정 (순서대로)

### (A) RealSense TOP — D435 입력
1. `RealSense TOP` 추가.
2. **Sensor** = `Depth`로 한 개, `Color`로 또 한 개 (TOP 2개 두는 게 편함).
   - 또는 한 개에서 Depth, 별도 `RealSense TOP`에서 Color.
3. D435 권장 해상도: **848×480 @ 30fps** (D435 깊이 정밀도 스위트스폿) 또는 640×480.
4. Depth 출력은 미터 단위라 값이 큼 → 다음 `Math TOP`으로 정규화:
   - `Math TOP` (Range): From `0 ~ 4`(m) → To `0 ~ 1`. 0.3~3m 정도가 사람 인식 범위.
   - 살짝 `Blur TOP` (size 2~3)로 깊이 노이즈 정리.

> D435 깊이엔 구멍/노이즈가 있어요. `Math`→`Blur` 한 번이면 충분합니다.
> 더 깔끔히 하려면 RealSense TOP의 **Hole Filling / Temporal** 후처리 옵션을 켜세요.

### (B) GLSL: 00_motion — 동작 감지
1. `GLSL TOP` 추가, 이름 `glsl_motion`.
2. 입력0 ← Color(또는 정규화 Depth), 입력1 ← **이 노드 출력을 1프레임 늦춘 것**.
   - 입력1은 `Cache TOP`(Cache Size 1) 또는 `Feedback TOP`을 거쳐 자기 출력을 받음.
3. `glsl/00_motion.frag` 내용을 Pixel Shader에 붙여넣기.
4. 커스텀 파라미터(Vectors/Floats 페이지)에 `uGain` 추가 → 4.0.

### (C) GLSL: 01_flowfield — 흐름장 ★
1. `GLSL TOP`, 이름 `glsl_flowfield`.
2. 입력0 ← 정규화된 Depth, 입력1 ← `glsl_motion` 출력.
3. `glsl/01_flowfield.frag` 붙여넣기.
4. 커스텀 uniform 파라미터 추가 (이름은 `u` 떼고 첫 글자 대문자 규칙):
   `uTime`(absTime.seconds 익스프레션), `uSwirl`=1.2, `uNoiseScale`=3,
   `uNoiseSpeed`=0.15, `uMotionForce`=2.2, `uDepthNear`=0.02, `uDepthFar`=0.95.
   - `uTime`은 파라미터 칸에 `absTime.seconds` 라고 입력(Expression 모드).
5. 해상도는 카메라와 동일(848×480)로.

### (D) GLSL: 02_advect — 붓터치 누적 ★ (Feedback 루프)
1. `GLSL TOP`, 이름 `glsl_advect`.
2. 입력0 ← **자기 출력의 Feedback** (아래 참고), 입력1 ← `glsl_flowfield`,
   입력2 ← Color(또는 04_palette를 거치기 전 Source 색; 단순히 RealSense Color 권장).
3. **Feedback 만들기**: `Feedback TOP` 하나 추가 → Target TOP을 `glsl_advect`로 지정
   → `Feedback TOP` 출력을 `glsl_advect`의 입력0에 연결. (자기 자신을 1프레임 지연으로 받음)
4. `glsl/02_advect.frag` 붙여넣기.
5. 커스텀 파라미터: `uFlowAmount`=0.004, `uInject`=0.10, `uFade`=0.975, `uDryBrush`=0.6.

> 이 피드백 루프가 "붓이 화면을 끌고 다니는" 핵심입니다. `uFade`를 1.0에 가깝게
> 할수록 잔상이 길게 남아 끈적한 임파스토, 낮추면 빠르게 사라지는 가벼운 터치.

### (E) GLSL: 03_kuwahara — 유화 질감
1. `GLSL TOP`, 이름 `glsl_kuwahara`. 입력0 ← `glsl_advect`.
2. `glsl/03_kuwahara.frag` 붙여넣기. 커스텀 `uRadius`=4 (3~6 권장, 클수록 무거움).

> 쿠와하라는 픽셀당 연산이 많습니다. 무거우면 앞단에서 `Resolution TOP`으로
> 720p 정도로 줄이거나 `uRadius`를 낮추세요.

### (F) GLSL: 04_palette — 고흐 색조
1. `Movie File In TOP` 추가 → `assets/vangogh_palette.png` 로드 (Play=off, 정지 이미지).
2. `GLSL TOP`, 이름 `glsl_palette`. 입력0 ← `glsl_kuwahara`, 입력1 ← 팔레트 Movie File In.
3. `glsl/04_palette.frag` 붙여넣기.
4. 커스텀 파라미터: `uUseClut`=1, `uStrength`=0.85, `uContrast`=1.15, `uGlow`=0.25.
   - 팔레트 PNG 없이 코드 내장 색을 쓰려면 `uUseClut`=0.

### (G) 출력
- `glsl_palette` → `Out TOP` 또는 `Window COMP`(전체화면/프로젝터). 완성!

---

## 3. 커스텀 파라미터 빠르게 만드는 법

각 GLSL TOP에서: 우측 파라미터 → **Common** 옆 톱니 또는 `+` → **Customize Component**
→ Float/Vector 추가 → 이름을 셰이더 uniform과 맞춤(`uSwirl` → 이름 `Swirl`).
TouchDesigner는 파라미터 이름 `Swirl` 을 GLSL의 `uniform float uSwirl` 에 자동 바인딩합니다.

또는 `python/params.py`의 프리셋을 `Text DAT`에 붙여넣고 Textport에서:
```python
import params
params.apply("starry_night")   # 또는 "calm_wheatfield", "storm"
```

---

## 4. 튜닝 가이드 (느낌 잡기)

| 원하는 느낌 | 만지는 값 |
|------------|-----------|
| 더 격렬한 소용돌이 | `Swirl` ↑, `NoiseSpeed` ↑ |
| 관람객 움직임에 더 민감 | `MotionForce` ↑, motion `uGain` ↑ |
| 끈적한 두꺼운 물감 | `Fade` → 0.99, `Radius` ↑ |
| 가볍고 빠른 붓 | `Fade` → 0.95, `Inject` ↑ |
| 더 노랗고 밝게 | `Glow` ↑, palette `Strength` ↑ |
| 사람만 칠하고 배경은 검게 | `DepthNear/Far`로 깊이 범위 좁히기 |

---

## 5. (선택) 심박수 연동 — 이 저장소의 `heart_rate_osc.py`

저장소 루트의 `heart_rate_osc.py`가 심박수를 OSC `/heart_rate`로 보냅니다.
TouchDesigner에서 `OSC In CHOP`(포트 9000)로 받아 붓터치에 생체 리듬을 입힐 수 있어요:

- 심박수 → `glsl_advect`의 `Inject`나 `glsl_flowfield`의 `Swirl`에 매핑
  (심장이 빠르게 뛰면 붓질이 격렬해짐).
- 심박수 → `glsl_palette`의 `Glow`/`Contrast` (긴장하면 더 강렬한 색).

예) OSC In CHOP → `Math CHOP`(60~120 BPM → 0.8~1.6) → `glsl_flowfield`의
`Swirl` 파라미터에 익스프레션 `op('oscin1')['heart_rate']` 식으로 연결.

---

## 6. 다음 단계 — 모네 / 다빈치로 확장

같은 파이프라인에서 **03·04단계만 교체**하면 화풍을 바꿀 수 있습니다.
- **모네**: kuwahara 대신 작은 색점 + 가우시안 블러(광학 블렌딩), 잔잔한 ripple.
- **다빈치**: advect 약하게 + 깊이맵을 그대로 명암(키아로스쿠로)으로, 윤곽 흐리게(스푸마토).

원하시면 모네·다빈치 셰이더와 화풍 전환 스위치도 이어서 만들어 드릴게요.

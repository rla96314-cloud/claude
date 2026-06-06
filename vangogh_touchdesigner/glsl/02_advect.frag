// =============================================================================
// 02_advect.frag  -  흐름장을 따라 색을 흘리는 이류(advection) / 피드백 셰이더
// =============================================================================
// 입력:
//   sTD2DInputs[0] : 이전 프레임 (Feedback TOP 결과)  <- 자기 자신의 출력
//   sTD2DInputs[1] : Flow Field (01_flowfield 결과)
//   sTD2DInputs[2] : Source 색 (RealSense Color, 또는 팔레트 적용된 색)
// 출력:
//   누적되어 흐르는 붓터치 streak 이미지
//
// 핵심 아이디어:
//   - 매 프레임 "이전 화면을 흐름 반대방향에서 끌어와" 잔상을 남긴다 => 붓 자국.
//   - 소량의 Source 색을 계속 주입(inject)하고, 살짝 감쇠(fade)시켜 무한 누적 방지.
//   - mask가 0인 곳은 빠르게 비워 배경이 깨끗하게 유지되도록.
// =============================================================================

uniform float uFlowAmount;   // 흐르는 거리(픽셀 환산 전 비율)  기본 0.004
uniform float uInject;       // 매 프레임 새 색 주입량          기본 0.10
uniform float uFade;         // 잔상 감쇠 (1=영원, 0.9=빠르게)  기본 0.97
uniform float uDryBrush;     // 붓 거칠기(주입 색 대비)         기본 0.6

out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;

    vec4 fld = texture(sTD2DInputs[1], uv);
    vec2 flow = fld.rg * 2.0 - 1.0;     // 방향
    float strength = fld.b;             // 세기
    float mask = fld.a;                 // 피사체 마스크

    // 흐름 반대방향에서 이전 색을 끌어온다 (semi-Lagrangian advection)
    vec2 prevUV = uv - flow * uFlowAmount * (0.3 + strength);
    vec4 prev = texture(sTD2DInputs[0], prevUV);

    // 새로 주입할 색
    vec4 src = texture(sTD2DInputs[2], uv);

    // 붓 거칠기: 흐름 세기에 따라 주입을 변조 -> 마른 붓 느낌
    float inject = uInject * mix(1.0, strength, uDryBrush) * mask;

    vec4 col = mix(prev * uFade, src, inject);

    // 마스크 밖은 천천히 비우기
    col = mix(col, vec4(0.0), (1.0 - mask) * 0.08);

    fragColor = TDOutputSwizzle(col);
}

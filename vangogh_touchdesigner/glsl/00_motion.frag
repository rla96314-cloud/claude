// =============================================================================
// 00_motion.frag  -  프레임 차이 기반 간단 동작 감지 (광류 대용)
// =============================================================================
// 입력:
//   sTD2DInputs[0] : 현재 프레임 (RealSense Color 또는 Depth, 흑백 권장)
//   sTD2DInputs[1] : 이전 프레임 (이 노드 출력의 1프레임 지연 = Cache/Feedback)
// 출력:
//   RG = 추정 이동 방향(0.5 중심), B = 움직임 크기
//
// 정밀한 광류는 아니지만, 좌우/상하 밝기 변화로 대략의 방향과 세기를 만들어
// 01_flowfield 에 "관람객의 움직임"을 난류로 흘려넣기에 충분하다.
// TouchDesigner 17+ 의 [Optical Flow TOP] 이 있으면 그걸 써도 됨.
// =============================================================================

uniform float uGain;   // 움직임 증폭   기본 4.0

out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    vec2 tx = uTD2DInfos[0].res.xy;

    float cur  = dot(texture(sTD2DInputs[0], uv).rgb, vec3(0.333));
    float prev = dot(texture(sTD2DInputs[1], uv).rgb, vec3(0.333));
    float diff = cur - prev;                       // 시간 변화

    // 공간 기울기로 변화의 방향을 추정 (간이 광류)
    float gx = dot(texture(sTD2DInputs[0], uv + vec2(tx.x,0)).rgb
                 - texture(sTD2DInputs[0], uv - vec2(tx.x,0)).rgb, vec3(0.333));
    float gy = dot(texture(sTD2DInputs[0], uv + vec2(0,tx.y)).rgb
                 - texture(sTD2DInputs[0], uv - vec2(0,tx.y)).rgb, vec3(0.333));

    vec2 g = vec2(gx, gy);
    float gl = max(dot(g, g), 1e-4);
    vec2 flow = -diff * g / gl * uGain;            // 광류 제약식 근사
    flow = clamp(flow, -1.0, 1.0);

    float mag = clamp(abs(diff) * uGain, 0.0, 1.0);
    fragColor = TDOutputSwizzle(vec4(flow * 0.5 + 0.5, mag, 1.0));
}

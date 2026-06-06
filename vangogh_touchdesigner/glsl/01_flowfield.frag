// =============================================================================
// 01_flowfield.frag  -  고흐풍 흐름장(Flow Field) 생성
// =============================================================================
// 입력:
//   sTD2DInputs[0] : Depth (RealSense D435 깊이맵, R 채널 사용, 0~1 정규화 권장)
//   sTD2DInputs[1] : Motion (선택) - 광류/프레임차 결과. 없으면 검은색 연결.
// 출력:
//   RG = 흐름 벡터(2D 방향), B = 흐름 세기, A = 마스크(피사체 영역)
//
// 핵심 아이디어:
//   - 깊이의 기울기(Sobel)를 구해 "등고선의 접선" 방향으로 90도 회전.
//     => 별이 빛나는 밤처럼 형태를 휘감는 소용돌이 결이 만들어짐.
//   - 거기에 시간 기반 컬(curl) 노이즈를 더해 가만히 있어도 살아 움직이게.
//   - RealSense 동작(Motion)을 난류로 주입 => 관람객이 움직이면 화면이 요동.
// =============================================================================

uniform float uTime;          // absTime.seconds 등 연결
uniform float uSwirl;         // 소용돌이 강도        (기본 1.0)
uniform float uNoiseScale;    // 컬 노이즈 공간 스케일 (기본 3.0)
uniform float uNoiseSpeed;    // 컬 노이즈 흐름 속도   (기본 0.15)
uniform float uMotionForce;   // 동작 난류 주입량     (기본 2.0)
uniform float uDepthNear;     // 마스크 근거리 컷오프  (기본 0.02)
uniform float uDepthFar;      // 마스크 원거리 컷오프  (기본 0.95)

out vec4 fragColor;

// --- 간단한 2D 해시 / 그라디언트 노이즈 ---------------------------------------
vec2 hash2(vec2 p){
    p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

float gnoise(vec2 p){
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(dot(hash2(i + vec2(0.0,0.0)), f - vec2(0.0,0.0)),
                   dot(hash2(i + vec2(1.0,0.0)), f - vec2(1.0,0.0)), u.x),
               mix(dot(hash2(i + vec2(0.0,1.0)), f - vec2(0.0,1.0)),
                   dot(hash2(i + vec2(1.0,1.0)), f - vec2(1.0,1.0)), u.x), u.y);
}

// 노이즈의 컬(curl)을 구해 발산 없는(소용돌이) 벡터장을 만든다
vec2 curlNoise(vec2 p){
    float e = 0.01;
    float n1 = gnoise(p + vec2(0.0, e));
    float n2 = gnoise(p - vec2(0.0, e));
    float n3 = gnoise(p + vec2(e, 0.0));
    float n4 = gnoise(p - vec2(e, 0.0));
    return vec2((n1 - n2), -(n3 - n4)) / (2.0 * e);
}

void main()
{
    vec2 uv  = vUV.st;
    vec2 tx  = uTD2DInfos[0].res.xy;   // 1픽셀 크기 (1/w, 1/h)

    // --- 깊이 Sobel 기울기 -----------------------------------------------------
    float dL = texture(sTD2DInputs[0], uv + vec2(-tx.x, 0.0)).r;
    float dR = texture(sTD2DInputs[0], uv + vec2( tx.x, 0.0)).r;
    float dD = texture(sTD2DInputs[0], uv + vec2(0.0, -tx.y)).r;
    float dU = texture(sTD2DInputs[0], uv + vec2(0.0,  tx.y)).r;
    float dC = texture(sTD2DInputs[0], uv).r;

    vec2 grad = vec2(dR - dL, dU - dD);           // 깊이 오르막 방향
    vec2 tangent = vec2(-grad.y, grad.x);         // 90도 회전 = 등고선 접선(소용돌이)

    // --- 컬 노이즈로 "살아있는" 결 추가 ---------------------------------------
    vec2 np = uv * uNoiseScale + vec2(uTime * uNoiseSpeed, 0.0);
    vec2 curl = curlNoise(np);

    // --- 동작 난류 주입 --------------------------------------------------------
    vec2 motion = texture(sTD2DInputs[1], uv).rg * 2.0 - 1.0; // -1~1
    float motionMag = length(motion);

    // --- 합성 -----------------------------------------------------------------
    vec2 flow = tangent * uSwirl
              + curl * 0.5
              + motion * uMotionForce;

    float mag = length(flow);
    if (mag > 1e-5) flow /= mag;                  // 방향만 남기고 정규화
    float strength = clamp(mag + motionMag * 0.5, 0.0, 1.0);

    // --- 피사체 마스크 (깊이 범위 안만 1) -------------------------------------
    float mask = step(uDepthNear, dC) * step(dC, uDepthFar);

    fragColor = TDOutputSwizzle(vec4(flow * 0.5 + 0.5, strength, mask));
}

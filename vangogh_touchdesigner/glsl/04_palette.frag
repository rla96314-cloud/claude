// =============================================================================
// 04_palette.frag  -  '별이 빛나는 밤' 팔레트 그레이딩
// =============================================================================
// 입력:
//   sTD2DInputs[0] : 색 이미지 (kuwahara 결과)
//   sTD2DInputs[1] : 팔레트 램프 (1xN CLUT, make_palette.py 로 생성) - 선택
// 출력:
//   고흐 색조로 매핑된 최종 이미지
//
// 두 가지 방식 지원:
//   1) CLUT 사용(uUseClut=1): 입력 밝기로 팔레트 램프를 룩업 => 색 통일감 최고
//   2) 절차적(uUseClut=0): 코드 내장 3색(짙은 인디고/코발트/크롬옐로) 보간
// =============================================================================

uniform float uUseClut;     // 1=CLUT 사용, 0=내장 팔레트
uniform float uStrength;    // 그레이딩 적용 강도 (0~1)  기본 0.85
uniform float uContrast;    // 명암 대비               기본 1.15
uniform float uGlow;        // 하이라이트 발광          기본 0.25

out vec4 fragColor;

vec3 vanGoghRamp(float t){
    // 별이 빛나는 밤: 그림자=짙은 인디고, 중간=코발트/청록, 하이라이트=크롬옐로
    vec3 shadow = vec3(0.043, 0.078, 0.235);  // deep indigo  #0B143C
    vec3 mid    = vec3(0.114, 0.353, 0.553);  // cobalt       #1D5A8D
    vec3 light  = vec3(0.953, 0.792, 0.231);  // chrome yellow#F3CA3B
    t = clamp(t, 0.0, 1.0);
    return (t < 0.5)
        ? mix(shadow, mid,  t * 2.0)
        : mix(mid,    light, (t - 0.5) * 2.0);
}

void main()
{
    vec2 uv = vUV.st;
    vec3 src = texture(sTD2DInputs[0], uv).rgb;

    // 밝기(룩업 키)
    float lum = dot(src, vec3(0.299, 0.587, 0.114));
    lum = clamp((lum - 0.5) * uContrast + 0.5, 0.0, 1.0);

    // 팔레트 색
    vec3 pal = (uUseClut > 0.5)
        ? texture(sTD2DInputs[1], vec2(lum, 0.5)).rgb
        : vanGoghRamp(lum);

    // 원본 색조를 약간 보존해 디테일 유지
    vec3 graded = mix(src, pal, uStrength);

    // 하이라이트 발광 (별빛 느낌)
    float hi = smoothstep(0.7, 1.0, lum);
    graded += hi * uGlow * vec3(1.0, 0.85, 0.4);

    fragColor = TDOutputSwizzle(vec4(graded, 1.0));
}

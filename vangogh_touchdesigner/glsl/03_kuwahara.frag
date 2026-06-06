// =============================================================================
// 03_kuwahara.frag  -  쿠와하라(Kuwahara) 필터 = 유화 임파스토 질감
// =============================================================================
// 입력:
//   sTD2DInputs[0] : 색 이미지 (advect 결과 또는 카메라 색)
// 출력:
//   납작한 색 면 + 또렷한 경계의 "유화로 칠한 듯한" 이미지
//
// 원리: 각 픽셀 주변을 4개 사분면으로 나눠 분산이 가장 작은(=가장 평탄한)
//       사분면의 평균색을 채택. 붓으로 뭉갠 듯한 면이 생긴다 => 임파스토.
// =============================================================================

uniform float uRadius;   // 붓 크기(픽셀)  기본 4.0 (클수록 거친 붓)

out vec4 fragColor;

void main()
{
    vec2 uv = vUV.st;
    vec2 tx = uTD2DInfos[0].res.xy;       // 1픽셀 크기
    int  r  = int(uRadius);

    vec3 mean[4];
    vec3 sqMean[4];
    for (int k = 0; k < 4; ++k){ mean[k] = vec3(0.0); sqMean[k] = vec3(0.0); }

    // 사분면 오프셋 범위
    // 0:좌하 1:우하 2:좌상 3:우상
    int xs[4] = int[](-r, 0, -r, 0);
    int ys[4] = int[](-r, -r, 0, 0);

    float n = float((r + 1) * (r + 1));

    for (int q = 0; q < 4; ++q){
        for (int j = 0; j <= r; ++j){
            for (int i = 0; i <= r; ++i){
                vec2 o = vec2(float(xs[q] + i), float(ys[q] + j)) * tx;
                vec3 c = texture(sTD2DInputs[0], uv + o).rgb;
                mean[q]   += c;
                sqMean[q] += c * c;
            }
        }
        mean[q]   /= n;
        sqMean[q] /= n;
    }

    // 분산이 최소인 사분면 선택
    vec3 result = mean[0];
    float minVar = 1e9;
    for (int q = 0; q < 4; ++q){
        vec3 var = sqMean[q] - mean[q] * mean[q];
        float v = var.r + var.g + var.b;
        if (v < minVar){ minVar = v; result = mean[q]; }
    }

    fragColor = TDOutputSwizzle(vec4(result, 1.0));
}

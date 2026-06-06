"""
파라미터 프리셋 모음.  TouchDesigner [Text DAT] 에 붙여넣고
아래 apply(op('...')) 식으로 각 GLSL TOP 의 커스텀 파라미터에 일괄 적용한다.

예) Textport 또는 Execute DAT 에서:
    import params
    params.apply_all()

전제: 가이드(README)대로 GLSL TOP 들에 커스텀 파라미터를 만들고,
      각 TOP 이름을 아래 NODES 와 맞춰 둔 경우.
"""

# (op이름, {파라미터명: 값})  - 파라미터명은 GLSL uniform 이름에서 'u' 떼고 사용
PRESETS = {
    "starry_night": {
        "glsl_flowfield": {"Swirl": 1.2, "Noisescale": 3.0, "Noisespeed": 0.15,
                            "Motionforce": 2.2, "Depthnear": 0.02, "Depthfar": 0.95},
        "glsl_advect":    {"Flowamount": 0.004, "Inject": 0.10, "Fade": 0.975,
                            "Drybrush": 0.6},
        "glsl_kuwahara":  {"Radius": 4.0},
        "glsl_palette":   {"Useclut": 1.0, "Strength": 0.85, "Contrast": 1.15,
                            "Glow": 0.25},
    },
    "calm_wheatfield": {   # 더 잔잔하고 노란 톤
        "glsl_flowfield": {"Swirl": 0.7, "Noisespeed": 0.08, "Motionforce": 1.2},
        "glsl_advect":    {"Fade": 0.985, "Inject": 0.07},
        "glsl_kuwahara":  {"Radius": 6.0},
        "glsl_palette":   {"Strength": 0.7, "Glow": 0.15},
    },
    "storm": {             # 동작에 격렬하게 반응
        "glsl_flowfield": {"Swirl": 1.6, "Motionforce": 3.5, "Noisespeed": 0.3},
        "glsl_advect":    {"Flowamount": 0.007, "Fade": 0.96, "Inject": 0.14},
        "glsl_kuwahara":  {"Radius": 3.0},
        "glsl_palette":   {"Contrast": 1.3, "Glow": 0.4},
    },
}


def apply(preset_name="starry_night"):
    """현재 .toe 안의 TOP 들에 프리셋 값을 적용한다 (TouchDesigner 내부 전용)."""
    preset = PRESETS[preset_name]
    for node_name, params in preset.items():
        n = op(node_name)               # noqa: F821  (op은 TD 전역)
        if n is None:
            print(f"[건너뜀] '{node_name}' 노드를 찾을 수 없음")
            continue
        for p, v in params.items():
            par = getattr(n.par, p, None)
            if par is None:
                print(f"[건너뜀] {node_name}.{p} 파라미터 없음")
                continue
            par.val = v
    print(f"프리셋 적용 완료: {preset_name}")


def apply_all():
    apply("starry_night")

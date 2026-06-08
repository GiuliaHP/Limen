Shader "Custom/SH_Distortion"
{
    Properties
    {
        _DistortionStrength ("Distortion Strength", Range(0, 0.2)) = 0.05
        _DistortionFreq ("Distortion Frequency", Float) = 12

        _EdgeRadius ("Edge Threshold", Range(0, 0.1)) = 0.01
        _EdgeSoftness ("Edge Softness", Range(0.0001, 0.1)) = 0.01
        _EdgeWidth ("Edge Width (px)", Range(1, 8)) = 2

        _SketchSpeed ("Sketch Speed", Float) = 1.5
        _SketchJitter ("Sketch Jitter", Range(0, 0.2)) = 0.06
    }

    HLSLINCLUDE
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
    #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

    CBUFFER_START(UnityPerMaterial)
        float _DistortionStrength;
        float _DistortionFreq;
        float _EdgeRadius;
        float _EdgeSoftness;
        float _EdgeWidth;
        float _SketchSpeed;
        float _SketchJitter;
    CBUFFER_END

    float Hash21(float2 p)
    {
        p = frac(p * float2(123.34, 456.21));
        p += dot(p, p + 45.32);
        return frac(p.x * p.y);
    }

    float DepthEdgeDelta(float2 uv, float2 texel)
    {
        float centerDepth = Linear01Depth(SampleSceneDepth(uv), _ZBufferParams);
        float depthRight = Linear01Depth(SampleSceneDepth(uv + float2(texel.x, 0.0)), _ZBufferParams);
        float depthLeft = Linear01Depth(SampleSceneDepth(uv - float2(texel.x, 0.0)), _ZBufferParams);
        float depthUp = Linear01Depth(SampleSceneDepth(uv + float2(0.0, texel.y)), _ZBufferParams);
        float depthDown = Linear01Depth(SampleSceneDepth(uv - float2(0.0, texel.y)), _ZBufferParams);

        return max(
            max(abs(centerDepth - depthRight), abs(centerDepth - depthLeft)),
            max(abs(centerDepth - depthUp), abs(centerDepth - depthDown))
        );
    }

    float4 Frag(Varyings input) : SV_Target
    {
        float time = _Time.y * _SketchSpeed;
        float2 uv = input.texcoord;

        float2 texel = _BlitTexture_TexelSize.xy;
        float2 wideTexel = texel * max(1.0, _EdgeWidth);
        float depthDelta = max(DepthEdgeDelta(uv, texel), DepthEdgeDelta(uv, wideTexel));
        float edgeMask = smoothstep(_EdgeRadius, _EdgeRadius + _EdgeSoftness, depthDelta);

        float2 sketchUV = uv * _DistortionFreq;
        float2 cell = floor(sketchUV);
        float lineA = sin((sketchUV.y + time * 1.7) * 6.28318 + Hash21(cell) * 6.28318);
        float lineB = cos((sketchUV.x - time * 1.3) * 6.28318 + Hash21(cell.yx + 17.0) * 6.28318);
        float grain = Hash21(sketchUV + time);

        float2 distortion = float2(lineA, lineB) * 0.65 + (grain - 0.5);
        distortion *= _SketchJitter * edgeMask;

        float4 baseColor = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, uv);
        float2 distortedUV = saturate(uv + distortion * _DistortionStrength);
        float4 borderColor = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_LinearClamp, distortedUV);

        float sketchPulse = 0.96 + 0.04 * sin(time * 2.0 + uv.y * 80.0);
        baseColor.rgb *= lerp(1.0, sketchPulse, edgeMask * 0.35);

        return lerp(baseColor, borderColor, edgeMask);
    }
    ENDHLSL

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline" = "UniversalPipeline"}
        LOD 100
        ZTest Always ZWrite Off Cull Off

        Pass
        {
            Name "EdgeDistortionPass"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            ENDHLSL
        }
    }
}
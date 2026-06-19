Shader "Custom/SH_SkyboxDissolve"
{
    Properties
    {
        _Tint ("Tint Color", Color) = (0.5, 0.5, 0.5, 0.5)
        [Gamma] _Exposure ("Exposure", Range(0, 8)) = 1.0
        _Rotation ("Rotation", Range(0, 360)) = 0.0
        [NoScaleOffset] _TexA ("Skybox A (HDR)", CUBE) = "grey" {}
        [NoScaleOffset] _TexB ("Skybox B (HDR)", CUBE) = "grey" {}
        _Transition_State ("Transition State", Range(0, 1)) = 0.0
        _DissolveNoiseScale ("Dissolve Noise Scale", Range(0.1, 20)) = 4.0
        _DissolveSoftness ("Dissolve Softness", Range(0.0001, 0.5)) = 0.03
        _NoiseScrollA ("Noise Scroll A", Vector) = (0.08, 0.02, 0.0, 0.0)
        _NoiseScrollB ("Noise Scroll B", Vector) = (-0.03, 0.09, 0.0, 0.0)
        _NoiseMix ("Noise Mix", Range(0, 1)) = 0.55
        _EdgeColor ("Edge Color", Color) = (1, 0.85, 0.55, 1)
        _EdgeIntensity ("Edge Intensity", Range(0, 8)) = 1.25
        _EdgeWidth ("Edge Width", Range(0.0001, 0.25)) = 0.035
    }

    SubShader
    {
        Tags { "Queue" = "Background" "RenderType" = "Background" "PreviewType" = "Skybox" }

        Cull Off
        ZWrite Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            samplerCUBE _TexA;
            float4 _TexA_HDR;
            samplerCUBE _TexB;
            float4 _TexB_HDR;
            float4 _Tint;
            float _Exposure;
            float _Rotation;
            float _Transition_State;
            float _DissolveNoiseScale;
            float _DissolveSoftness;
            float4 _NoiseScrollA;
            float4 _NoiseScrollB;
            float _NoiseMix;
            float4 _EdgeColor;
            float _EdgeIntensity;
            float _EdgeWidth;

            struct appdata
            {
                float4 vertex : POSITION;
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 dir : TEXCOORD0;
            };

            v2f vert(appdata v)
            {
                v2f o;
                o.pos = UnityObjectToClipPos(v.vertex);

                float radiansRotation = radians(_Rotation);
                float sinRotation = sin(radiansRotation);
                float cosRotation = cos(radiansRotation);
                float3 direction = v.vertex.xyz;

                o.dir = float3(
                    cosRotation * direction.x - sinRotation * direction.z,
                    direction.y,
                    sinRotation * direction.x + cosRotation * direction.z
                );

                return o;
            }

            float Hash31(float3 p)
            {
                p = frac(p * 0.1031);
                p += dot(p, p.yzx + 33.33);
                return frac((p.x + p.y) * p.z);
            }

            float Noise3D(float3 p)
            {
                float3 i = floor(p);
                float3 f = frac(p);
                float3 u = f * f * (3.0 - 2.0 * f);

                float n000 = Hash31(i + float3(0.0, 0.0, 0.0));
                float n100 = Hash31(i + float3(1.0, 0.0, 0.0));
                float n010 = Hash31(i + float3(0.0, 1.0, 0.0));
                float n110 = Hash31(i + float3(1.0, 1.0, 0.0));
                float n001 = Hash31(i + float3(0.0, 0.0, 1.0));
                float n101 = Hash31(i + float3(1.0, 0.0, 1.0));
                float n011 = Hash31(i + float3(0.0, 1.0, 1.0));
                float n111 = Hash31(i + float3(1.0, 1.0, 1.0));

                float x00 = lerp(n000, n100, u.x);
                float x10 = lerp(n010, n110, u.x);
                float x01 = lerp(n001, n101, u.x);
                float x11 = lerp(n011, n111, u.x);

                float y0 = lerp(x00, x10, u.y);
                float y1 = lerp(x01, x11, u.y);

                return lerp(y0, y1, u.z);
            }

            fixed4 frag(v2f i) : SV_Target
            {
                float3 direction = normalize(i.dir);
                fixed3 skyboxA = DecodeHDR(texCUBE(_TexA, direction), _TexA_HDR);
                fixed3 skyboxB = DecodeHDR(texCUBE(_TexB, direction), _TexB_HDR);

                float time = _Time.y;
                float3 noiseSpace = direction * _DissolveNoiseScale;
                float3 movingNoiseA = noiseSpace + float3(_NoiseScrollA.xy * time, 0.0);
                float3 movingNoiseB = noiseSpace + float3(_NoiseScrollB.xy * time, 0.0) + float3(17.0, 31.0, 59.0);

                float noiseA = Noise3D(movingNoiseA);
                float noiseB = Noise3D(movingNoiseB);
                float combinedNoise = lerp(noiseA, noiseB, saturate(_NoiseMix));

                float dissolve = step(_Transition_State, combinedNoise);
                float edgeDistance = abs(combinedNoise - _Transition_State);
                float edgeMask = saturate(1.0 - edgeDistance / _EdgeWidth);
                edgeMask = edgeMask * edgeMask;

                fixed3 skyColor = lerp(skyboxA, skyboxB, dissolve);
                skyColor += _EdgeColor.rgb * (_EdgeIntensity * edgeMask);
                skyColor *= _Tint.rgb * _Exposure;

                return fixed4(skyColor, 1.0);
            }
            ENDCG
        }
    }

    Fallback Off
}

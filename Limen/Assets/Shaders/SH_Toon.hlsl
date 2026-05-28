float ToonSafeSteps(float steps)
{
    return max(steps, 2.0);
}

float ToonQuantize01(float value, float steps)
{
    float safeSteps = ToonSafeSteps(steps);
    float clampedValue = saturate(value);
    return floor(clampedValue * safeSteps) / (safeSteps - 1.0);
}

void ToonPosterize_float(float3 color, float steps, out float3 outColor)
{
    float safeSteps = ToonSafeSteps(steps);
    float3 clampedColor = saturate(color);
    outColor = floor(clampedColor * safeSteps) / (safeSteps - 1.0);
}

void ToonCelShade_float(float3 color, float steps, float shadowFloor, out float3 outColor)
{
    float safeSteps = ToonSafeSteps(steps);
    float3 clampedColor = saturate(color);
    float luminance = dot(clampedColor, float3(0.2126, 0.7152, 0.0722));
    float band = floor(saturate(luminance) * safeSteps) / (safeSteps - 1.0);
    float shade = lerp(saturate(shadowFloor), 1.0, band);
    outColor = clampedColor * shade;
}

void ToonCelShadeWithTint_float(float3 color, float3 shadowTint, float steps, float shadowFloor, out float3 outColor)
{
    float safeSteps = ToonSafeSteps(steps);
    float3 clampedColor = saturate(color);
    float luminance = dot(clampedColor, float3(0.2126, 0.7152, 0.0722));
    float band = floor(saturate(luminance) * safeSteps) / (safeSteps - 1.0);
    float shade = lerp(saturate(shadowFloor), 1.0, band);
    outColor = lerp(saturate(shadowTint), clampedColor, shade);
}
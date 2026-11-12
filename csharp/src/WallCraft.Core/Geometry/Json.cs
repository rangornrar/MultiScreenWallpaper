using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace WallCraft.Core.Geometry;

/// <summary>Lecture tolérante de valeurs JSON et écriture compatible avec <c>json.dumps</c> de Python.</summary>
internal static class Json
{
    public static double? Number(JsonNode? node)
    {
        if (node is not JsonValue v) return null;
        if (v.GetValueKind() != JsonValueKind.Number) return null;
        return v.TryGetValue(out double d) && double.IsFinite(d) ? d : null;
    }

    public static bool? Bool(JsonNode? node) => node is JsonValue v && v.GetValueKind() is JsonValueKind.True or JsonValueKind.False
        ? v.GetValue<bool>() : null;

    public static string? String(JsonNode? node) => node is JsonValue v && v.GetValueKind() == JsonValueKind.String ? v.GetValue<string>() : null;

    /// <summary>Chaîne JSON comme <c>json.dumps</c> (ensure_ascii=True) : tout caractère hors ASCII en \uXXXX minuscule.</summary>
    public static string PythonDumpsString(string value)
    {
        var sb = new StringBuilder(value.Length + 2).Append('"');
        foreach (char ch in value)
        {
            switch (ch)
            {
                case '"': sb.Append("\\\""); break;
                case '\\': sb.Append("\\\\"); break;
                case '\n': sb.Append("\\n"); break;
                case '\r': sb.Append("\\r"); break;
                case '\t': sb.Append("\\t"); break;
                case '\b': sb.Append("\\b"); break;
                case '\f': sb.Append("\\f"); break;
                default:
                    if (ch < 0x20 || ch > 0x7e) sb.Append("\\u").Append(((int)ch).ToString("x4", CultureInfo.InvariantCulture));
                    else sb.Append(ch);
                    break;
            }
        }
        return sb.Append('"').ToString();
    }
}

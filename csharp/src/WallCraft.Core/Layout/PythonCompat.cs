using System.Globalization;
using System.Numerics;
using System.Security.Cryptography;
using System.Text;

namespace WallCraft.Core.Layout;

/// <summary>
/// Petites fonctions de Python reproduites exactement, pour retrouver les mêmes graines et
/// les mêmes calculs que la version Python : <c>round</c>, <c>sum</c> (Neumaier), <c>repr</c>.
/// </summary>
public static class PythonCompat
{
    /// <summary><c>round(x)</c> : entier le plus proche, égalités vers le pair.</summary>
    public static long RoundToInt(double x) => (long)Math.Round(x, MidpointRounding.ToEven);

    /// <summary>
    /// <c>round(x, ndigits)</c> : arrondi correct sur la valeur binaire EXACTE (égalités vers le pair),
    /// comme CPython. <c>Math.Round(x, n)</c> multiplie par 10ⁿ et peut se tromper d'un cran.
    /// </summary>
    public static double Round(double x, int ndigits)
    {
        if (double.IsNaN(x) || double.IsInfinity(x) || x == 0) return x;
        if (ndigits < 0) throw new ArgumentOutOfRangeException(nameof(ndigits));
        long bits = BitConverter.DoubleToInt64Bits(x);
        bool negative = bits < 0;
        int exponent = (int)((bits >> 52) & 0x7FF);
        long mantissa = bits & 0xFFFFFFFFFFFFFL;
        if (exponent == 0) exponent++; else mantissa |= 1L << 52;
        exponent -= 1075; // x = mantissa × 2^exponent

        // x × 10^n = num / den, exactement
        BigInteger num = new BigInteger(mantissa) * BigInteger.Pow(10, ndigits);
        BigInteger den = BigInteger.One;
        if (exponent >= 0) num <<= exponent; else den <<= -exponent;

        BigInteger q = BigInteger.DivRem(num, den, out BigInteger r);
        int cmp = (r * 2).CompareTo(den);
        if (cmp > 0 || (cmp == 0 && !q.IsEven)) q += 1;

        // q / 10^n, conversion correctement arrondie par l'analyseur de .NET
        double result = double.Parse($"{q}E-{ndigits}", NumberStyles.Float, CultureInfo.InvariantCulture);
        return negative ? -result : result;
    }

    /// <summary><c>sum()</c> de flottants depuis Python 3.12 : somme compensée de Neumaier.</summary>
    public static double Sum(IEnumerable<double> values)
    {
        double result = 0.0, c = 0.0;
        foreach (var x in values)
        {
            double t = result + x;
            if (Math.Abs(result) >= Math.Abs(x)) c += (result - t) + x;
            else c += (x - t) + result;
            result = t;
        }
        if (c != 0 && double.IsFinite(c)) result += c;
        return result;
    }

    /// <summary><c>repr(float)</c> : plus courte écriture exacte, avec « .0 » et exposant à la manière de Python.</summary>
    public static string ReprFloat(double x)
    {
        if (double.IsNaN(x)) return "nan";
        if (double.IsPositiveInfinity(x)) return "inf";
        if (double.IsNegativeInfinity(x)) return "-inf";
        if (x == 0) return BitConverter.DoubleToInt64Bits(x) < 0 ? "-0.0" : "0.0";

        // « R » donne les chiffres significatifs les plus courts ; on les remet en forme comme Python.
        string shortest = Math.Abs(x).ToString("R", CultureInfo.InvariantCulture);
        // Chiffres et exposant décimal à partir de l'écriture la plus courte
        string mantissaPart = shortest;
        int exp10 = 0;
        int ePos = shortest.IndexOfAny(['E', 'e']);
        if (ePos >= 0)
        {
            mantissaPart = shortest[..ePos];
            exp10 = int.Parse(shortest[(ePos + 1)..], CultureInfo.InvariantCulture);
        }
        int dot = mantissaPart.IndexOf('.');
        string intPart = dot >= 0 ? mantissaPart[..dot] : mantissaPart;
        string fracPart = dot >= 0 ? mantissaPart[(dot + 1)..] : "";
        string digits = (intPart + fracPart).TrimStart('0');
        int leadingZerosRemoved = (intPart + fracPart).Length - digits.Length;
        digits = digits.TrimEnd('0');
        if (digits.Length == 0) digits = "0";
        // valeur = 0.d1d2… × 10^decpt
        int decpt = intPart.Length - leadingZerosRemoved + exp10;

        string body;
        if (decpt > -4 && decpt <= 16)
        {
            if (decpt <= 0) body = "0." + new string('0', -decpt) + digits;
            else if (decpt >= digits.Length) body = digits + new string('0', decpt - digits.Length) + ".0";
            else body = digits[..decpt] + "." + digits[decpt..];
        }
        else
        {
            int e = decpt - 1;
            string m = digits.Length == 1 ? digits : digits[0] + "." + digits[1..];
            body = m + "e" + (e < 0 ? "-" : "+") + Math.Abs(e).ToString("00", CultureInfo.InvariantCulture);
        }
        return (x < 0 ? "-" : "") + body;
    }

    /// <summary><c>repr(str)</c> : guillemets simples sauf si le texte contient « ' » et pas « " », échappements de CPython.</summary>
    public static string ReprString(string value)
    {
        char quote = value.Contains('\'') && !value.Contains('"') ? '"' : '\'';
        var sb = new StringBuilder(value.Length + 2);
        sb.Append(quote);
        for (int i = 0; i < value.Length; i++)
        {
            char ch = value[i];
            int cp = ch;
            if (char.IsHighSurrogate(ch) && i + 1 < value.Length && char.IsLowSurrogate(value[i + 1]))
            {
                cp = char.ConvertToUtf32(ch, value[i + 1]);
                i++;
            }
            if (cp == quote || cp == '\\') sb.Append('\\').Append((char)cp);
            else if (cp == '\t') sb.Append("\\t");
            else if (cp == '\n') sb.Append("\\n");
            else if (cp == '\r') sb.Append("\\r");
            else if (cp < 0x20 || cp == 0x7f) sb.Append("\\x").Append(cp.ToString("x2", CultureInfo.InvariantCulture));
            else if (cp < 0x7f) sb.Append((char)cp);
            else if (IsPrintable(cp)) sb.Append(char.ConvertFromUtf32(cp));
            else if (cp <= 0xff) sb.Append("\\x").Append(cp.ToString("x2", CultureInfo.InvariantCulture));
            else if (cp <= 0xffff) sb.Append("\\u").Append(cp.ToString("x4", CultureInfo.InvariantCulture));
            else sb.Append("\\U").Append(cp.ToString("x8", CultureInfo.InvariantCulture));
        }
        sb.Append(quote);
        return sb.ToString();
    }

    /// <summary>Approximation de <c>str.isprintable()</c> : ni contrôle, ni format, ni séparateur (hors espace), ni privé, ni non attribué.</summary>
    private static bool IsPrintable(int cp)
    {
        if (cp >= 0xD800 && cp <= 0xDFFF) return false;
        var cat = CharUnicodeInfo.GetUnicodeCategory(cp);
        return cat switch
        {
            UnicodeCategory.Control or UnicodeCategory.Format or UnicodeCategory.Surrogate
                or UnicodeCategory.PrivateUse or UnicodeCategory.OtherNotAssigned
                or UnicodeCategory.LineSeparator or UnicodeCategory.ParagraphSeparator => false,
            UnicodeCategory.SpaceSeparator => cp == ' ',
            _ => true,
        };
    }

    /// <summary><c>int(hashlib.sha1(texte.encode()).hexdigest()[:12], 16)</c>.</summary>
    public static long Sha1Prefix48(string text)
    {
        byte[] hash = SHA1.HashData(Encoding.UTF8.GetBytes(text));
        long value = 0;
        for (int i = 0; i < 6; i++) value = (value << 8) | hash[i];
        return value;
    }
}

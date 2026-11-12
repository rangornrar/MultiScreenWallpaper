using WallCraft.Core.Layout;

namespace WallCraft.Core.Tests;

/// <summary>Valeurs obtenues avec CPython 3.12 ; les fichiers de référence complets sont testés à part.</summary>
public class PythonCompatTests
{
    [Test]
    public void RandomMatchesCPython()
    {
        var cases = new (long Seed, double Random, int RandInt, uint Bits)[]
        {
            (0, 0.8444218515250481, 7, 1911784257),
            (42, 0.6394267984578837, 1, 1592467581),
            (4294967301, 0.15727238718789782, 3, 1911101237),
            (0x1234567890ab, 0.9499690417741931, 1, 322883857),
        };
        foreach (var c in cases)
        {
            var r = new PythonRandom(c.Seed);
            Assert.Equal(c.Random, r.Random(), $"random() graine {c.Seed}");
            Assert.Equal(c.RandInt, r.RandInt(1, 7), $"randint graine {c.Seed}");
            Assert.Equal(c.Bits, r.GetRandBits(31), $"getrandbits graine {c.Seed}");
        }
    }

    [Test]
    public void ShuffleChoiceUniformMatchCPython()
    {
        var r = new PythonRandom(7);
        var list = Enumerable.Range(0, 10).ToList();
        r.Shuffle(list);
        Assert.SequenceEqual([8, 3, 1, 4, 7, 0, 9, 6, 2, 5], list);
        Assert.Equal(true, r.Choice(new[] { true, false }));
        Assert.Equal(-0.09250086831160304, r.Uniform(-0.1, 0.1));
    }

    [Test]
    public void RoundIsExactHalfEven()
    {
        Assert.Equal(0.0312, PythonCompat.Round(0.03125, 4));
        Assert.Equal(2.67, PythonCompat.Round(2.675, 2)); // 2.675 vaut en réalité 2.67499999…
        Assert.Equal(1.7778, PythonCompat.Round(1.77777777, 4));
    }

    [Test]
    public void ReprFloatLikePython()
    {
        Assert.Equal("1e-05", PythonCompat.ReprFloat(1e-05));
        Assert.Equal("1e+16", PythonCompat.ReprFloat(1e16));
        Assert.Equal("1.2345678901234568e+17", PythonCompat.ReprFloat(123456789012345678.0));
        Assert.Equal("0.0001", PythonCompat.ReprFloat(0.0001));
        Assert.Equal("1.0", PythonCompat.ReprFloat(1.0));
        Assert.Equal("0.5625", PythonCompat.ReprFloat(0.5625));
        Assert.Equal("6175.0", PythonCompat.ReprFloat(6175.0));
        Assert.Equal("-2.5", PythonCompat.ReprFloat(-2.5));
    }

    [Test]
    public void ReprStringLikePython()
    {
        Assert.Equal("\"C:\\\\Users\\\\l'été\\\\b.png\"", PythonCompat.ReprString("C:\\Users\\l'été\\b.png"));
        Assert.Equal("'a\"b\\'c'", PythonCompat.ReprString("a\"b'c"));
        Assert.Equal("'日本\\x7f\\u200b'", PythonCompat.ReprString("日本\u007f\u200b"));
    }

    [Test]
    public void SumIsCompensatedLikePython312()
    {
        Assert.Equal(1.0, PythonCompat.Sum(Enumerable.Repeat(0.1, 10)));
        Assert.Equal(1.0, PythonCompat.Sum([1e16, 1.0, -1e16]));
    }
}

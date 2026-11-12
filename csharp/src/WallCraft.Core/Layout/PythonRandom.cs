using System.Numerics;

namespace WallCraft.Core.Layout;

/// <summary>
/// Portage exact de <c>random.Random</c> de CPython (Mersenne Twister MT19937, graine entière via
/// <c>init_by_array</c>). Indispensable pour que la version C# produise les mêmes dispositions
/// « aléatoires reproductibles » que la version Python, au bit près.
/// Seules les fonctions utilisées par le moteur de disposition sont portées.
/// </summary>
public sealed class PythonRandom
{
    private const int N = 624;
    private const int M = 397;
    private const uint MatrixA = 0x9908b0dfU;
    private const uint UpperMask = 0x80000000U;
    private const uint LowerMask = 0x7fffffffU;

    private readonly uint[] _mt = new uint[N];
    private int _index = N + 1;

    public PythonRandom(BigInteger seed) => Seed(seed);

    public PythonRandom(long seed) : this(new BigInteger(seed)) { }

    /// <summary>Équivalent de <c>random.seed(n)</c> pour un entier : la valeur absolue est découpée en mots de 32 bits.</summary>
    public void Seed(BigInteger seed)
    {
        var n = BigInteger.Abs(seed);
        var key = new List<uint>();
        if (n.IsZero)
        {
            key.Add(0);
        }
        else
        {
            while (!n.IsZero)
            {
                key.Add((uint)(n & uint.MaxValue));
                n >>= 32;
            }
        }
        InitByArray(key);
    }

    /// <summary>État interne (pour les tests) : les mots et l'index, comme <c>getstate()</c>.</summary>
    internal (uint[] Words, int Index) State => ((uint[])_mt.Clone(), _index);

    private void InitGenrand(uint s)
    {
        _mt[0] = s;
        for (int i = 1; i < N; i++)
            _mt[i] = unchecked(1812433253U * (_mt[i - 1] ^ (_mt[i - 1] >> 30)) + (uint)i);
        _index = N;
    }

    private void InitByArray(IReadOnlyList<uint> key)
    {
        InitGenrand(19650218U);
        int i = 1, j = 0;
        int keyLength = key.Count;
        for (int k = Math.Max(N, keyLength); k > 0; k--)
        {
            _mt[i] = unchecked((_mt[i] ^ ((_mt[i - 1] ^ (_mt[i - 1] >> 30)) * 1664525U)) + key[j] + (uint)j);
            i++; j++;
            if (i >= N) { _mt[0] = _mt[N - 1]; i = 1; }
            if (j >= keyLength) j = 0;
        }
        for (int k = N - 1; k > 0; k--)
        {
            _mt[i] = unchecked((_mt[i] ^ ((_mt[i - 1] ^ (_mt[i - 1] >> 30)) * 1566083941U)) - (uint)i);
            i++;
            if (i >= N) { _mt[0] = _mt[N - 1]; i = 1; }
        }
        _mt[0] = 0x80000000U;
        _index = N;
    }

    /// <summary>Mot de 32 bits suivant (<c>genrand_uint32</c>).</summary>
    public uint NextUInt32()
    {
        uint y;
        if (_index >= N)
        {
            int kk;
            for (kk = 0; kk < N - M; kk++)
            {
                y = (_mt[kk] & UpperMask) | (_mt[kk + 1] & LowerMask);
                _mt[kk] = _mt[kk + M] ^ (y >> 1) ^ ((y & 1U) != 0 ? MatrixA : 0U);
            }
            for (; kk < N - 1; kk++)
            {
                y = (_mt[kk] & UpperMask) | (_mt[kk + 1] & LowerMask);
                _mt[kk] = _mt[kk + (M - N)] ^ (y >> 1) ^ ((y & 1U) != 0 ? MatrixA : 0U);
            }
            y = (_mt[N - 1] & UpperMask) | (_mt[0] & LowerMask);
            _mt[N - 1] = _mt[M - 1] ^ (y >> 1) ^ ((y & 1U) != 0 ? MatrixA : 0U);
            _index = 0;
        }

        y = _mt[_index++];
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c5680U;
        y ^= (y << 15) & 0xefc60000U;
        y ^= y >> 18;
        return y;
    }

    /// <summary><c>random()</c> : flottant dans [0, 1) sur 53 bits.</summary>
    public double Random()
    {
        uint a = NextUInt32() >> 5, b = NextUInt32() >> 6;
        return (a * 67108864.0 + b) * (1.0 / 9007199254740992.0);
    }

    /// <summary><c>getrandbits(k)</c> pour 0 ≤ k ≤ 32.</summary>
    public uint GetRandBits(int k)
    {
        if (k < 0 || k > 32) throw new ArgumentOutOfRangeException(nameof(k), "0 ≤ k ≤ 32");
        if (k == 0) return 0;
        return NextUInt32() >> (32 - k);
    }

    /// <summary><c>_randbelow(n)</c> : entier uniforme dans [0, n), par rejet comme CPython.</summary>
    public int RandBelow(int n)
    {
        if (n <= 0) throw new ArgumentOutOfRangeException(nameof(n));
        int k = 32 - BitOperations.LeadingZeroCount((uint)n); // n.bit_length()
        uint r = GetRandBits(k);
        while (r >= (uint)n) r = GetRandBits(k);
        return (int)r;
    }

    /// <summary><c>randint(a, b)</c>, bornes incluses.</summary>
    public int RandInt(int a, int b)
    {
        if (b < a) throw new ArgumentException("b < a");
        return a + RandBelow(b - a + 1);
    }

    /// <summary><c>shuffle(x)</c> en place (Fisher-Yates de CPython, du dernier élément vers le premier).</summary>
    public void Shuffle<T>(IList<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--)
        {
            int j = RandBelow(i + 1);
            (list[i], list[j]) = (list[j], list[i]);
        }
    }

    /// <summary><c>choice(seq)</c>.</summary>
    public T Choice<T>(IReadOnlyList<T> seq) => seq[RandBelow(seq.Count)];

    /// <summary><c>sample(population, k)</c> : k éléments distincts, même algorithme que CPython 3.12.</summary>
    public List<T> Sample<T>(IReadOnlyList<T> population, int k)
    {
        int n = population.Count;
        if (k < 0 || k > n) throw new ArgumentOutOfRangeException(nameof(k), "échantillon plus grand que la population");
        var result = new T[k];
        int setSize = 21;
        if (k > 5) setSize += (int)Math.Pow(4, Math.Ceiling(Math.Log(k * 3) / Math.Log(4)));
        if (n <= setSize)
        {
            var pool = population.ToList();
            for (int i = 0; i < k; i++)
            {
                int j = RandBelow(n - i);
                result[i] = pool[j];
                pool[j] = pool[n - i - 1];
            }
        }
        else
        {
            var selected = new HashSet<int>();
            for (int i = 0; i < k; i++)
            {
                int j = RandBelow(n);
                while (selected.Contains(j)) j = RandBelow(n);
                selected.Add(j);
                result[i] = population[j];
            }
        }
        return [.. result];
    }

    /// <summary><c>uniform(a, b)</c>.</summary>
    public double Uniform(double a, double b) => a + (b - a) * Random();
}

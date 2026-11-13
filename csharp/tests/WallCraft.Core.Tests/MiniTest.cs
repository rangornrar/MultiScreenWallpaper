using System.Diagnostics;
using System.Reflection;

namespace WallCraft.Core.Tests;

/// <summary>Marque une méthode publique sans paramètre comme test.</summary>
[AttributeUsage(AttributeTargets.Method)]
public sealed class TestAttribute : Attribute { }

public sealed class AssertionException(string message) : Exception(message);

/// <summary>Assertions minimales (pas de paquet NuGet nécessaire).</summary>
public static class Assert
{
    public static void True(bool condition, string? message = null)
    {
        if (!condition) throw new AssertionException(message ?? "condition fausse");
    }

    public static void Equal<T>(T expected, T actual, string? message = null)
    {
        if (!EqualityComparer<T>.Default.Equals(expected, actual))
            throw new AssertionException($"{message} attendu <{expected}>, obtenu <{actual}>".Trim());
    }

    public static void Near(double expected, double actual, double tolerance = 1e-9, string? message = null)
    {
        if (double.IsNaN(actual) || Math.Abs(expected - actual) > tolerance)
            throw new AssertionException($"{message} attendu {expected:R} ± {tolerance}, obtenu {actual:R}".Trim());
    }

    public static void SequenceEqual<T>(IEnumerable<T> expected, IEnumerable<T> actual, string? message = null)
    {
        var e = expected.ToList();
        var a = actual.ToList();
        if (!e.SequenceEqual(a))
            throw new AssertionException($"{message} attendu [{string.Join(", ", e)}], obtenu [{string.Join(", ", a)}]".Trim());
    }

    public static TException Throws<TException>(Action action) where TException : Exception
    {
        try { action(); }
        catch (TException ex) { return ex; }
        throw new AssertionException($"exception {typeof(TException).Name} attendue");
    }
}

/// <summary>Chemin des fichiers de référence copiés à côté de l'exécutable de test.</summary>
public static class Fixtures
{
    public static string Path(string name) => System.IO.Path.Combine(AppContext.BaseDirectory, "fixtures", name);
    public static bool Exists(string name) => File.Exists(Path(name));
}

public static class Program
{
    /// <summary>Lance tous les tests (ou ceux dont le nom contient l'argument). Code retour 1 en cas d'échec.</summary>
    public static int Main(string[] args)
    {
        var filter = args.FirstOrDefault();
        var tests = typeof(Program).Assembly.GetTypes()
            .SelectMany(t => t.GetMethods(BindingFlags.Public | BindingFlags.Instance | BindingFlags.Static)
                .Where(m => m.GetCustomAttribute<TestAttribute>() != null)
                .Select(m => (Type: t, Method: m)))
            .Where(x => filter == null || $"{x.Type.Name}.{x.Method.Name}".Contains(filter, StringComparison.OrdinalIgnoreCase))
            .OrderBy(x => x.Type.Name).ThenBy(x => x.Method.Name)
            .ToList();

        int failed = 0;
        var clock = Stopwatch.StartNew();
        foreach (var (type, method) in tests)
        {
            var name = $"{type.Name}.{method.Name}";
            try
            {
                var instance = method.IsStatic ? null : Activator.CreateInstance(type);
                method.Invoke(instance, null);
                Console.WriteLine($"OK    {name}");
            }
            catch (TargetInvocationException ex)
            {
                failed++;
                var inner = ex.InnerException ?? ex;
                Console.WriteLine($"ÉCHEC {name}\n      {inner.GetType().Name}: {inner.Message}");
                if (inner is not AssertionException) Console.WriteLine(inner.StackTrace);
            }
        }
        Console.WriteLine($"\n{tests.Count - failed}/{tests.Count} tests réussis en {clock.Elapsed.TotalSeconds:F1} s");
        return failed == 0 && tests.Count > 0 ? 0 : 1;
    }
}

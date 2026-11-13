namespace WallCraft.Core.Tests;

public class SmokeTests
{
    [Test]
    public void SchemaVersionMatchesPython() => Assert.Equal(1, CoreInfo.ProjectSchemaVersion);
}

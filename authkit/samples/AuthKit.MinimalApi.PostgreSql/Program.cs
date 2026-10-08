var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => Results.Ok(new
{
    sample = "AuthKit.MinimalApi.PostgreSql",
    stage = "Host scaffold; authentication and PostgreSQL integration pending",
    browserPrefix = "/auth/browser",
    bearerPrefix = "/auth/bearer"
}));

app.MapGet("/health/live", () => Results.Ok(new { status = "alive" }));

app.Run();

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.UseDefaultFiles();
app.UseStaticFiles();
app.MapGet("/health/live", () => Results.Ok(new { status = "alive" }));

app.Run();

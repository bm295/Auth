using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using System.Text.Encodings.Web;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

const string JwtScheme = "JwtDemo";
const string ApiKeyScheme = "ApiKeyDemo";
const string BasicScheme = "BasicDemo";
const string DemoIssuer = "AuthDemoIssuer";
const string DemoAudience = "AuthDemoAudience";
const string DemoJwtKey = "ThisIsADemoJwtSigningKey1234567890!";
const string DemoApiKey = "demo-api-key-123";
const string DemoBasicUser = "demo";
const string DemoBasicPassword = "password";

var signingKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(DemoJwtKey));

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultScheme = CookieAuthenticationDefaults.AuthenticationScheme;
    })
    .AddCookie(options =>
    {
        options.LoginPath = "/auth/cookie/login";
    })
    .AddJwtBearer(JwtScheme, options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = DemoIssuer,
            ValidateAudience = true,
            ValidAudience = DemoAudience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = signingKey,
            ValidateLifetime = true,
            ClockSkew = TimeSpan.Zero
        };
    })
    .AddScheme<AuthenticationSchemeOptions, ApiKeyAuthenticationHandler>(ApiKeyScheme, _ => { })
    .AddScheme<AuthenticationSchemeOptions, BasicAuthenticationHandler>(BasicScheme, _ => { });

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", () => Results.Content(StaticContent.Html, "text/html"));

app.MapGet("/auth/jwt/token", () =>
{
    var claims = new[]
    {
        // Keep JWT registered claims explicit so Java consumers receive the same contract.
        new Claim(JwtRegisteredClaimNames.Sub, "manager@contoso.demo"),
        new Claim(ClaimTypes.Name, "JWT Demo User"),
        new Claim("tenant_id", "contoso"),
        new Claim("role", "reader"),
        new Claim("auth_method", "jwt")
    };

    var creds = new SigningCredentials(signingKey, SecurityAlgorithms.HmacSha256);
    var expiresAt = DateTime.UtcNow.AddMinutes(20);
    var token = new JwtSecurityToken(
        issuer: DemoIssuer,
        audience: DemoAudience,
        claims: claims,
        expires: expiresAt,
        signingCredentials: creds);

    return Results.Ok(new
    {
        method = "JWT",
        howItWorks = "Server signs a token. Client stores and sends it in Authorization header.",
        usage = "Authorization: Bearer <token>",
        expiresAt,
        token = new JwtSecurityTokenHandler().WriteToken(token)
    });
});

app.MapPost("/auth/cookie/login", async (HttpContext context) =>
{
    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, "cookie-user-1"),
        new Claim(ClaimTypes.Name, "Cookie Demo User"),
        new Claim("auth_method", "cookie")
    };

    var identity = new ClaimsIdentity(claims, CookieAuthenticationDefaults.AuthenticationScheme);
    await context.SignInAsync(CookieAuthenticationDefaults.AuthenticationScheme, new ClaimsPrincipal(identity));

    return Results.Ok(new
    {
        method = "Cookie Session",
        howItWorks = "Server creates an auth cookie after login. Browser sends cookie automatically.",
        note = "This response sets a cookie in your browser."
    });
});

app.MapPost("/auth/cookie/logout", async (HttpContext context) =>
{
    await context.SignOutAsync(CookieAuthenticationDefaults.AuthenticationScheme);
    return Results.Ok(new { message = "Signed out. Cookie removed." });
});

app.MapGet("/auth/apikey/demo", () => Results.Ok(new
{
    method = "API Key",
    howItWorks = "Client sends a static key. Server validates it.",
    headerName = "X-API-Key",
    apiKey = DemoApiKey
}));

app.MapGet("/auth/basic/demo", () =>
{
    var raw = $"{DemoBasicUser}:{DemoBasicPassword}";
    var encoded = Convert.ToBase64String(Encoding.UTF8.GetBytes(raw));
    return Results.Ok(new
    {
        method = "Basic Auth",
        howItWorks = "Client sends base64(username:password) each request.",
        usage = $"Authorization: Basic {encoded}",
        username = DemoBasicUser,
        password = DemoBasicPassword
    });
});

app.MapGet("/demo/protected/jwt", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "JWT auth succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(p => p.AddAuthenticationSchemes(JwtScheme).RequireAuthenticatedUser());

app.MapGet("/demo/protected/cookie", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "Cookie auth succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(p => p.AddAuthenticationSchemes(CookieAuthenticationDefaults.AuthenticationScheme).RequireAuthenticatedUser());

app.MapGet("/demo/protected/apikey", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "API key auth succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(p => p.AddAuthenticationSchemes(ApiKeyScheme).RequireAuthenticatedUser());

app.MapGet("/demo/protected/basic", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "Basic auth succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(p => p.AddAuthenticationSchemes(BasicScheme).RequireAuthenticatedUser());

app.Run();

sealed class ApiKeyAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    private const string HeaderName = "X-API-Key";
    private const string ExpectedApiKey = "demo-api-key-123";

    public ApiKeyAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        ISystemClock clock)
        : base(options, logger, encoder, clock)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue(HeaderName, out var value))
        {
            return Task.FromResult(AuthenticateResult.Fail("Missing X-API-Key header."));
        }

        if (!string.Equals(value.ToString(), ExpectedApiKey, StringComparison.Ordinal))
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid API key."));
        }

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, "apikey-user-1"),
            new Claim(ClaimTypes.Name, "API Key Demo User"),
            new Claim("auth_method", "apikey")
        };

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var ticket = new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name);
        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

sealed class BasicAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    private const string ExpectedUser = "demo";
    private const string ExpectedPassword = "password";

    public BasicAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        UrlEncoder encoder,
        ISystemClock clock)
        : base(options, logger, encoder, clock)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue("Authorization", out var authHeader))
        {
            return Task.FromResult(AuthenticateResult.Fail("Missing Authorization header."));
        }

        var raw = authHeader.ToString();
        if (!raw.StartsWith("Basic ", StringComparison.OrdinalIgnoreCase))
        {
            return Task.FromResult(AuthenticateResult.Fail("Authorization must use Basic."));
        }

        var encoded = raw["Basic ".Length..].Trim();
        string decoded;
        try
        {
            decoded = Encoding.UTF8.GetString(Convert.FromBase64String(encoded));
        }
        catch
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid Basic token encoding."));
        }

        var sep = decoded.IndexOf(':');
        if (sep <= 0)
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid Basic token format."));
        }

        var user = decoded[..sep];
        var pass = decoded[(sep + 1)..];

        if (!string.Equals(user, ExpectedUser, StringComparison.Ordinal) ||
            !string.Equals(pass, ExpectedPassword, StringComparison.Ordinal))
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid username or password."));
        }

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, "basic-user-1"),
            new Claim(ClaimTypes.Name, "Basic Demo User"),
            new Claim("auth_method", "basic")
        };

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var ticket = new AuthenticationTicket(new ClaimsPrincipal(identity), Scheme.Name);
        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

static class StaticContent
{
    public const string Html = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Authentication Playground</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: #fffaf0;
      --ink: #1f2937;
      --accent: #c2410c;
      --muted: #6b7280;
      --line: #e5d7bf;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 10%, #ffe7c2 0, transparent 35%),
        radial-gradient(circle at 90% 20%, #ffe2d2 0, transparent 30%),
        var(--bg);
      min-height: 100vh;
    }
    .wrap { max-width: 980px; margin: 0 auto; padding: 24px; }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
    }
    h1 { margin-top: 0; }
    .methods { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; }
    button {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 10px;
      padding: 10px 12px;
      cursor: pointer;
      font-weight: 600;
    }
    button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
    .actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
    pre {
      background: #121826;
      color: #e5edf7;
      padding: 12px;
      border-radius: 10px;
      overflow: auto;
      white-space: pre-wrap;
      word-break: break-word;
      min-height: 120px;
    }
    .small { color: var(--muted); font-size: .95rem; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>Authentication Playground</h1>
      <p class="small">Select an auth method, view how it works, then run a real protected API call.</p>
      <div class="methods" id="methods"></div>
    </div>

    <div class="card">
      <h2 id="methodTitle"></h2>
      <p id="explanation" class="small"></p>
      <div id="hint" class="small"></div>
      <div class="actions" id="actions"></div>
    </div>

    <div class="card">
      <h2>Response</h2>
      <pre id="output">Choose a method to start.</pre>
    </div>
  </div>

  <script>
    const methods = {
      jwt: {
        name: 'JWT',
        explain: 'JWT is signed by the server. Client sends it in Authorization: Bearer <token>.',
        hint: 'Steps: Get token -> Call protected endpoint with Bearer token.',
        actions: [
          { label: 'Get JWT Token', run: getJwtToken },
          { label: 'Call JWT Protected API', run: callJwtProtected }
        ]
      },
      cookie: {
        name: 'Cookie Session',
        explain: 'After login, server sets an auth cookie. Browser sends cookie automatically.',
        hint: 'Steps: Login (set cookie) -> Call protected endpoint -> Logout.',
        actions: [
          { label: 'Login (Set Cookie)', run: cookieLogin },
          { label: 'Call Cookie Protected API', run: callCookieProtected },
          { label: 'Logout', run: cookieLogout }
        ]
      },
      apikey: {
        name: 'API Key',
        explain: 'Client sends a static key, often in X-API-Key header.',
        hint: 'Steps: Get demo key -> Call protected endpoint with X-API-Key.',
        actions: [
          { label: 'Show Demo API Key', run: showApiKey },
          { label: 'Call API Key Protected API', run: callApiKeyProtected }
        ]
      },
      basic: {
        name: 'Basic Auth',
        explain: 'Client sends base64(username:password) in every request.',
        hint: 'Steps: Show demo credentials -> Call protected endpoint with Basic header.',
        actions: [
          { label: 'Show Basic Credentials', run: showBasic },
          { label: 'Call Basic Protected API', run: callBasicProtected }
        ]
      }
    };

    let current = 'jwt';
    let jwtToken = '';
    let apiKey = '';
    let basicHeader = '';

    function setOutput(data) {
      const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
      document.getElementById('output').textContent = text;
    }

    function renderMethods() {
      const root = document.getElementById('methods');
      root.innerHTML = '';
      Object.entries(methods).forEach(([id, item]) => {
        const b = document.createElement('button');
        b.textContent = item.name;
        b.className = current === id ? 'active' : '';
        b.onclick = () => { current = id; render(); };
        root.appendChild(b);
      });
    }

    function renderActions() {
      const root = document.getElementById('actions');
      root.innerHTML = '';
      methods[current].actions.forEach(a => {
        const b = document.createElement('button');
        b.textContent = a.label;
        b.onclick = async () => {
          try { await a.run(); } catch (err) { setOutput(String(err)); }
        };
        root.appendChild(b);
      });
    }

    function render() {
      renderMethods();
      document.getElementById('methodTitle').textContent = methods[current].name;
      document.getElementById('explanation').textContent = methods[current].explain;
      document.getElementById('hint').textContent = methods[current].hint;
      renderActions();
      setOutput('Ready: ' + methods[current].name);
    }

    async function parseResponse(resp) {
      const text = await resp.text();
      try { return JSON.parse(text); } catch { return { status: resp.status, body: text }; }
    }

    async function getJwtToken() {
      const resp = await fetch('/auth/jwt/token');
      const data = await parseResponse(resp);
      jwtToken = data.token || '';
      setOutput(data);
    }

    async function callJwtProtected() {
      if (!jwtToken) return setOutput('Get JWT token first.');
      const resp = await fetch('/demo/protected/jwt', { headers: { Authorization: `Bearer ${jwtToken}` } });
      setOutput(await parseResponse(resp));
    }

    async function cookieLogin() {
      const resp = await fetch('/auth/cookie/login', { method: 'POST' });
      setOutput(await parseResponse(resp));
    }

    async function cookieLogout() {
      const resp = await fetch('/auth/cookie/logout', { method: 'POST' });
      setOutput(await parseResponse(resp));
    }

    async function callCookieProtected() {
      const resp = await fetch('/demo/protected/cookie');
      setOutput(await parseResponse(resp));
    }

    async function showApiKey() {
      const resp = await fetch('/auth/apikey/demo');
      const data = await parseResponse(resp);
      apiKey = data.apiKey || '';
      setOutput(data);
    }

    async function callApiKeyProtected() {
      if (!apiKey) return setOutput('Fetch demo API key first.');
      const resp = await fetch('/demo/protected/apikey', { headers: { 'X-API-Key': apiKey } });
      setOutput(await parseResponse(resp));
    }

    async function showBasic() {
      const resp = await fetch('/auth/basic/demo');
      const data = await parseResponse(resp);
      basicHeader = data.usage ? data.usage.replace('Authorization: ', '') : '';
      setOutput(data);
    }

    async function callBasicProtected() {
      if (!basicHeader) return setOutput('Show credentials first.');
      const resp = await fetch('/demo/protected/basic', { headers: { Authorization: basicHeader } });
      setOutput(await parseResponse(resp));
    }

    render();
  </script>
</body>
</html>
""";
}

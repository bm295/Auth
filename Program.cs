using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;

var builder = WebApplication.CreateBuilder(args);

const string JwtScheme = "JwtDemo";
const string OpaqueBearerScheme = "OpaqueBearerDemo";
const string DemoIssuer = "MahjongDemoIssuer";
const string DemoAudience = "MahjongDemoAudience";
const string DemoSigningKey = "ThisIsASecureDemoKeyForJwtSigning123!";
const string OpaqueTokenValue = "demo-opaque-token";

var keyBytes = Encoding.UTF8.GetBytes(DemoSigningKey);

builder.Services
    .AddAuthentication(options =>
    {
        options.DefaultScheme = OpaqueBearerScheme;
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
            IssuerSigningKey = new SymmetricSecurityKey(keyBytes),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.Zero
        };
    })
    .AddScheme<AuthenticationSchemeOptions, OpaqueBearerAuthenticationHandler>(OpaqueBearerScheme, _ => { });

builder.Services.AddAuthorization();

var app = builder.Build();

app.UseAuthentication();
app.UseAuthorization();

app.MapGet("/", () => Results.Content(HtmlPage, "text/html"));

app.MapGet("/auth/jwt/token", () =>
{
    var credentials = new SigningCredentials(new SymmetricSecurityKey(keyBytes), SecurityAlgorithms.HmacSha256);
    var claims = new[]
    {
        new Claim(ClaimTypes.NameIdentifier, "demo-user"),
        new Claim(ClaimTypes.Name, "JWT Demo User"),
        new Claim("auth_type", "jwt")
    };

    var tokenDescriptor = new JwtSecurityToken(
        issuer: DemoIssuer,
        audience: DemoAudience,
        claims: claims,
        expires: DateTime.UtcNow.AddMinutes(20),
        signingCredentials: credentials);

    var token = new JwtSecurityTokenHandler().WriteToken(tokenDescriptor);
    return Results.Ok(new
    {
        authType = "JWT",
        scheme = JwtScheme,
        token,
        usage = "Authorization: Bearer <token>"
    });
});

app.MapGet("/auth/opaque/token", () => Results.Ok(new
{
    authType = "Opaque Bearer",
    scheme = OpaqueBearerScheme,
    token = OpaqueTokenValue,
    usage = "Authorization: Bearer demo-opaque-token"
}));

app.MapGet("/demo/protected/jwt", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "JWT authentication succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(policy => policy.AddAuthenticationSchemes(JwtScheme).RequireAuthenticatedUser());

app.MapGet("/demo/protected/opaque", (ClaimsPrincipal user) => Results.Ok(new
{
    message = "Opaque Bearer authentication succeeded.",
    user = user.Identity?.Name,
    claims = user.Claims.Select(c => new { c.Type, c.Value })
})).RequireAuthorization(policy => policy.AddAuthenticationSchemes(OpaqueBearerScheme).RequireAuthenticatedUser());

app.Run();

sealed class OpaqueBearerAuthenticationHandler : AuthenticationHandler<AuthenticationSchemeOptions>
{
    private const string ExpectedToken = "demo-opaque-token";

    public OpaqueBearerAuthenticationHandler(
        IOptionsMonitor<AuthenticationSchemeOptions> options,
        ILoggerFactory logger,
        System.Text.Encodings.Web.UrlEncoder encoder,
        ISystemClock clock)
        : base(options, logger, encoder, clock)
    {
    }

    protected override Task<AuthenticateResult> HandleAuthenticateAsync()
    {
        if (!Request.Headers.TryGetValue("Authorization", out var headerValue))
        {
            return Task.FromResult(AuthenticateResult.Fail("Missing Authorization header."));
        }

        var raw = headerValue.ToString();
        if (!raw.StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        {
            return Task.FromResult(AuthenticateResult.Fail("Authorization header must use Bearer scheme."));
        }

        var token = raw["Bearer ".Length..].Trim();
        if (!string.Equals(token, ExpectedToken, StringComparison.Ordinal))
        {
            return Task.FromResult(AuthenticateResult.Fail("Invalid opaque bearer token."));
        }

        var claims = new[]
        {
            new Claim(ClaimTypes.NameIdentifier, "opaque-user"),
            new Claim(ClaimTypes.Name, "Opaque Token User"),
            new Claim("auth_type", "opaque")
        };

        var identity = new ClaimsIdentity(claims, Scheme.Name);
        var principal = new ClaimsPrincipal(identity);
        var ticket = new AuthenticationTicket(principal, Scheme.Name);

        return Task.FromResult(AuthenticateResult.Success(ticket));
    }
}

const string HtmlPage = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>.NET Auth Demo</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 960px; }
    .card { border: 1px solid #ddd; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; }
    button { margin-right: .5rem; margin-top: .5rem; }
    pre { background: #f7f7f7; padding: .75rem; border-radius: 6px; overflow:auto; }
    code { word-break: break-all; }
  </style>
</head>
<body>
  <h1>Authentication Demo (.NET)</h1>
  <p>Choose an authentication type and test protected endpoints.</p>

  <div class=\"card\">
    <h2>1) Select Authentication Type</h2>
    <button onclick=\"setType('jwt')\">JWT</button>
    <button onclick=\"setType('opaque')\">Opaque Bearer</button>
    <p>Current type: <strong id=\"type\">jwt</strong></p>
  </div>

  <div class=\"card\">
    <h2>2) Get Demo Token</h2>
    <button onclick=\"getToken()\">Get Token</button>
    <p><strong>Token:</strong></p>
    <pre><code id=\"token\">(none)</code></pre>
  </div>

  <div class=\"card\">
    <h2>3) Call Protected Endpoint</h2>
    <button onclick=\"callProtected()\">Call Endpoint</button>
    <p><strong>Response:</strong></p>
    <pre id=\"result\">(none)</pre>
  </div>

  <script>
    let selectedType = 'jwt';
    let token = '';

    function setType(type) {
      selectedType = type;
      document.getElementById('type').textContent = type;
      token = '';
      document.getElementById('token').textContent = '(none)';
      document.getElementById('result').textContent = '(none)';
    }

    async function getToken() {
      const endpoint = selectedType === 'jwt' ? '/auth/jwt/token' : '/auth/opaque/token';
      const response = await fetch(endpoint);
      const data = await response.json();
      token = data.token;
      document.getElementById('token').textContent = token;
    }

    async function callProtected() {
      if (!token) {
        document.getElementById('result').textContent = 'Get token first.';
        return;
      }

      const endpoint = selectedType === 'jwt' ? '/demo/protected/jwt' : '/demo/protected/opaque';
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      const text = await response.text();
      document.getElementById('result').textContent = text;
    }
  </script>
</body>
</html>
""";

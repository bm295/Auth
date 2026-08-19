# .NET Authentication Demo

This repository is rewritten as an ASP.NET Core web application that demonstrates two authentication approaches:

- JWT bearer token authentication
- Opaque bearer token authentication (custom handler)

## Run

```bash
dotnet run
```

Open the app at `http://localhost:5000` (or the URL shown by `dotnet run`).

## Remote API key validation and circuit breaker

By default, the playground validates the demo API key in memory. To validate it
through an external service, configure its base URL:

```bash
ApiKeyValidation__BaseUrl=https://identity.example.com/ dotnet run
```

The application sends `POST api-keys/validate` with a JSON body such as
`{"apiKey":"..."}`. The service should return `{"isValid":true}` for a valid key,
`401`/`403` for an invalid key, and a non-success status for a dependency failure.
The outbound client uses the .NET standard resilience pipeline, including timeout,
retry, and circuit-breaker strategies.

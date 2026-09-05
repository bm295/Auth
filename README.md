# .NET Authentication Demo

This repository is rewritten as an ASP.NET Core web application that demonstrates two authentication approaches:

- JWT bearer token authentication
- Opaque bearer token authentication (custom handler)

## Run

```bash
dotnet run
```

Open the app at `http://localhost:5000` (or the URL shown by `dotnet run`).

## Java JWT library

The reusable JWT contract is implemented for Java in [`java/auth-jwt-library`](java/auth-jwt-library). It validates the same HS256 issuer, audience, expiry, and signature used by this demo, and exposes the verified `sub` and custom claims.

Install it to the local Maven repository before building a Java consumer:

```bash
cd java/auth-jwt-library
mvn install
```

Its Maven coordinates are `com.authdemo:auth-jwt-library:1.0.0-SNAPSHOT`. The JWT endpoint now emits the `sub` user claim and `tenant_id` claim expected by the Asset service.

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

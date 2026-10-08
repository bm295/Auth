# Hợp đồng public API v1

Task P03, ngày 08/10/2026. Đây là hợp đồng thiết kế để triển khai A04–A09 và H01–H16; chưa phải API chạy được. Package identity theo [quyết định naming](package-naming.md). Use cases theo [phạm vi v1](product-scope-v1.md).

## Quy ước chung

- Target `net10.0`, nullable enabled, async I/O dùng `Task` và `CancellationToken` ở tham số cuối.
- ID dùng Guid; timestamp dùng DateTimeOffset UTC; thời lượng cấu hình dùng TimeSpan.
- Services không phụ thuộc HttpContext. Caller server được tin cậy chịu trách nhiệm tạo actor từ session đã xác thực và áp dụng authorization.
- Không bind public service command trực tiếp từ HTTP body nếu có actor/user ID hoặc metadata được server kiểm soát.
- Command/DTO có secret là sealed class với `ToString()` redacted, không dùng positional record mặc định in password/token. Không log destructuring các object đó.
- Validation/domain failures dùng `AuthResult<T>`; cancellation ném OperationCanceledException. Infrastructure failures ném `AuthDependencyException` đã sanitize, host mapping thành 503; không giả thành bad credentials. Không xác thực thành công khi dependency lỗi.

## Public DTO và kết quả

Các type trong `LocalSessions.AuthKit.Core.Contracts`:

| Type | Hợp đồng dữ liệu |
| --- | --- |
| AuthResult<T> | IsSuccess, Value khi thành công, Error khi thất bại; không cho phép đồng thời value và error |
| AuthError | Code ổn định, optional FieldErrors chứa mã validation; không chứa secrets, DB exception hoặc trạng thái tài khoản chi tiết |
| AuthSuccess | Marker thành công cho command không có payload |
| AuthUser | Id, Email, IsEmailVerified; không password hash hoặc security version |
| AuthSession | Id, CreatedAt, LastSeenAt, IdleExpiresAt, AbsoluteExpiresAt, DeviceLabel, IsCurrent; không digest/raw token |
| SessionPage | Items, NextCursor; phân trang theo thứ tự ổn định |
| AuthActor | UserId, SessionId; chỉ tạo trong trusted server sau validate; không dùng như bằng chứng auth độc lập |
| ValidatedSession | Actor, User, Session metadata; kết quả session validation |
| SessionGrant | User, Session, SecretToken; SecretToken là wrapper redacted, chỉ expose raw value có chủ đích khi phát credential |
| SessionContext | DeviceLabel và optional IP/UserAgent có giới hạn độ dài; lấy từ trusted server, chỉ là metadata |

`SessionGrant` là kết quả nội bộ tích hợp. Không serialize trực tiếp nó ở endpoint; browser chỉ nhận User/Session còn token được đặt vào cookie. Bearer profile trả raw token đúng một lần trong DTO phát hành riêng.

Commands gồm `RegisterCommand(Email, Password)`, `LoginCommand(Email, Password, SessionContext)`, `ConfirmEmailCommand(Token)`, `ResetPasswordCommand(Token, NewPassword)`, `ChangePasswordCommand(CurrentPassword, NewPassword)`. Các command có constructor/properties, validation và redaction theo quy ước trên, không dùng record tự sinh ToString cho secret.

## Account services

Namespace `LocalSessions.AuthKit.Core`:

```csharp
public interface IAuthService
{
    Task<AuthResult<AuthSuccess>> RegisterAsync(RegisterCommand command, CancellationToken cancellationToken = default);
    Task<AuthResult<SessionGrant>> LoginAsync(LoginCommand command, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> ResendVerificationAsync(string email, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> ConfirmEmailAsync(ConfirmEmailCommand command, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> RequestPasswordResetAsync(string email, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> ResetPasswordAsync(ResetPasswordCommand command, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> ChangePasswordAsync(AuthActor actor, ChangePasswordCommand command, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthUser>> GetCurrentUserAsync(AuthActor actor, CancellationToken cancellationToken = default);
}

public interface IAccountAdministrationService
{
    Task<AuthResult<AuthSuccess>> DisableUserAsync(Guid userId, CancellationToken cancellationToken = default);
}
```

Register/resend/forgot trả cùng dạng accepted thành công cho email không tồn tại hoặc email đã được sử dụng theo từng luồng; không trả UserId để anonymous caller dò tài khoản. Validation định dạng input vẫn có lỗi rõ ràng. Các command có actor recheck session/user active trong service để tránh actor stale; adapter store bảo vệ race theo security version. Host chịu trách nhiệm authorization trước khi gọi DisableUserAsync; thư viện không map admin endpoint công khai.

## Session services

```csharp
public interface ISessionService
{
    Task<AuthResult<ValidatedSession>> ValidateAsync(SecretToken token, CancellationToken cancellationToken = default);
    Task<AuthResult<SessionPage>> ListAsync(AuthActor actor, SessionListQuery query, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> RevokeAsync(AuthActor actor, Guid sessionId, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> RevokeCurrentAsync(SecretToken token, CancellationToken cancellationToken = default);
    Task<AuthResult<AuthSuccess>> RevokeAllAsync(AuthActor actor, CancellationToken cancellationToken = default);
}
```

Validate cập nhật LastSeen có throttle, không vượt absolute expiry. Invalid/missing/expired/revoked token dùng cùng lỗi Unauthenticated. RevokeCurrent chấp nhận token đã revoked/expired/không tồn tại và trả success sau input validation; không dùng thao tác này để xác nhận token tồn tại. Revoke với session ID không thuộc actor trả success không thao tác, giống session không tồn tại, tránh lộ thông tin ownership. List chỉ lấy session active của actor, cursor opaque, default 20/max 100 items.

## Adapter contracts

| Interface | Yêu cầu tối thiểu |
| --- | --- |
| IPasswordHasher | HashAsync và VerifyAsync; Verify trả Failed/Success/SuccessRehashNeeded; input wrapper redacted; không expose thuật toán tự viết |
| IAuthEmailSender | SendAsync(AuthEmailMessage, CancellationToken); message gồm loại, recipient, link, idempotency key; secret payload redacted |
| IAuthAuditSink | WriteAsync(AuthAuditEvent, CancellationToken); metadata allowlist, không secrets |
| IAuthStore | Atomic account creation + verification outbox; token replacement; consume verification; reset password + consume/revoke tokens/sessions; conditional password rehash/change; conditional create session; lookup/touch/revoke/list; disable user; outbox claim/complete/retry và cleanup |
| IAuthRateLimiter | AcquireAsync(operation, partition, CancellationToken) trả Allowed hoặc RetryAfter; partition từ trusted host, không chứa email raw |
| IAuthMaintenanceService | DispatchOutboxBatchAsync và CleanupBatchAsync với giới hạn batch/cancellation; host chủ động schedule |

IAuthStore là SPI dành cho adapter authors, không phải CRUD public cho endpoint. D05/A06 chốt signatures theo schema/transaction ADR P05 trước implementation. Shared contract tests phải kiểm tra atomicity, security-version checks, outbox claim lease chống worker tranh chấp, retry và cleanup. P03 chốt trách nhiệm và invariant của SPI; không đánh dấu A06 hoặc D05 hoàn thành.

## Options và DI contract

| Options | Giá trị mặc định hoặc yêu cầu |
| --- | --- |
| AuthOptions.Password | MinLength đề xuất 15, MaxLength 1024, không truncate/ép composition; hasher work factor benchmark ở U01 |
| AuthOptions.Account | RequireVerifiedEmail=true |
| AuthOptions.Session | IdleTimeout=30 phút, AbsoluteLifetime=7 ngày, LastSeenUpdateInterval=1 phút; IdleTimeout <= AbsoluteLifetime |
| AuthOptions.ActionTokens | VerificationLifetime=24 giờ, ResetLifetime=30 phút, ResendCooldown=1 phút |
| AuthOptions.Email | PublicBaseUri bắt buộc HTTPS production, fixed host-controlled routes, không lấy Host header |
| AuthKitAuthenticationOptions | Cookie hoặc OpaqueBearer; không thay default scheme trừ khi host chủ động chọn |
| AuthKitCookieOptions | __Host-AuthKit, HttpOnly=true, Secure=true, SameSite=Lax, Path=/, không Domain; development profile riêng |
| AuthKitEndpointOptions | Prefix=/auth, profile bắt buộc, EnabledFeatures; client không tự chọn profile qua request body |

Các options được validate khi startup, không chấp nhận thời lượng không dương hoặc cấu hình cookie production không an toàn. Constructor/default chi tiết và rate-limit quotas chốt trong A07/O05, không suy ra quota từ bảng này.

Extension methods dự kiến:

```csharp
// Namespace .DependencyInjection của package tương ứng.
services.AddAuthKit(options => { /* core options */ });
services.AddAuthKitPostgreSql(connectionString);
services.AddAuthKitAuthentication(options => { /* explicit schemes */ });
services.AddAuthKitMaintenance(options => { /* opt-in workers */ });
app.MapAuthKitEndpoints(options => { /* prefix + explicit profile */ });
```

AddAuthKit đăng ký core use cases và Microsoft password-hasher adapter dùng package Microsoft.Extensions.Identity.Core, không yêu cầu web runtime. ASP.NET-specific options/handlers/endpoints nằm trong AspNetCore. Missing store/email sender/required configuration phải báo lỗi startup rõ ràng. Services/store dùng scoped; TimeProvider dùng singleton; worker tạo scope theo batch. Chi tiết overload và adapter registrations được triển khai ở A09/H08.

## HTTP mapping

Body DTO chỉ chứa dữ liệu do client được phép gửi. Actor lấy từ ClaimsPrincipal được handler xác thực, SessionContext được host xây dựng. Browser và bearer endpoints dùng prefix riêng nếu bật cả hai, ví dụ `/auth/browser` và `/auth/bearer`; không dùng request field `mode` để chuyển credential transport.

| Method/path tương đối | Body/query | Thành công |
| --- | --- | --- |
| GET /antiforgery | Browser profile, không auth bắt buộc | 200 request token + antiforgery cookie; no-store |
| POST /register | email, password | 202 accepted chung |
| POST /login | email, password | 200 browser: user/session + Set-Cookie; bearer: user/session/token/tokenType=Bearer |
| POST /email/resend | email | 202 accepted chung |
| POST /email/confirm | token | 204 |
| POST /password/forgot | email | 202 accepted chung |
| POST /password/reset | token, newPassword | 204 |
| POST /password/change | currentPassword, newPassword | 204, thu hồi toàn bộ session và xóa browser cookie |
| GET /me | none | 200 AuthUser |
| GET /sessions | cursor, limit | 200 SessionPage |
| DELETE /sessions/{id} | session ID trên route | 204; nếu current session, xóa browser cookie |
| POST /logout | credential transport đã cấu hình | 204, revoke + clear cookie; expired/missing session cũng 204 |
| POST /logout-all | none | 204, revoke all + clear cookie |

Browser profile yêu cầu antiforgery ở tất cả unsafe methods, kể cả anonymous login/register/reset/logout. Logout idempotent không bỏ qua antiforgery. Sau login, client lấy request token mới gắn identity mới trước request unsafe tiếp theo. Các HTTP DTO có password/token phải redacted; action token gửi POST body, không tiêu thụ ở GET.

| AuthError.Code | HTTP |
| --- | --- |
| ValidationFailed | 400 |
| InvalidActionToken | 400 chung cho expired/consumed/wrong purpose |
| InvalidCredentials | 401 chung cho login rejected |
| Unauthenticated | 401 |
| Forbidden | 403 |
| RateLimited | 429 + Retry-After khi có giá trị |
| Conflict | 409 cho tranh chấp operation đã xác thực; không dùng để tiết lộ duplicate email anonymous |

Infrastructure failure: 503 sanitized ProblemDetails. Antiforgery failure: 400 với code riêng `AntiforgeryFailed`. ProblemDetails có `code` và correlation id; field errors chỉ cho validation. Không trả raw token trong lỗi. Responses nhạy cảm dùng no-store, không redirects. Request đã authenticate trước revoke có thể đang chạy; cam kết revoke áp dụng cho lần xác thực tiếp theo, không hủy ngược request đang thực thi.

## Quy tắc phát triển API

P03 định nghĩa hợp đồng để triển khai, không tạo stub library hoặc khẳng định code examples compile. A10 tạo public API baseline từ assemblies thật; mọi đổi signature/response/semantics phải cập nhật tài liệu, samples và tests. Invariants bảo mật trong scope v1 không được giảm khi tinh chỉnh SPI/overloads.

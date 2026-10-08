# Kế hoạch xây dựng thư viện Authentication bằng C#

Ngày lập: 08/10/2026. Trạng thái: đã hoàn thành P01–P07; các task chưa đánh dấu vẫn chờ triển khai.

## 1. Mục tiêu và quyết định sản phẩm

Xây dựng bộ thư viện NuGet **LocalSessions AuthKit**, nhúng trực tiếp vào backend .NET. Ứng dụng sử dụng sở hữu database, cấu hình và hạ tầng triển khai. Thư viện cung cấp API đăng ký, đăng nhập, xác minh email, khôi phục mật khẩu và quản lý session; tích hợp với authentication/authorization pipeline có sẵn của ASP.NET Core.

Package và namespace dùng prefix `LocalSessions.AuthKit` theo [quyết định naming P04](../authkit/docs/package-naming.md). Tên thư mục/project/solution tiếp tục dùng AuthKit; kiểm tra quyền publish lại ở R09 trước phát hành.

### Phạm vi v1.0

- Email/password, email verification, password reset và thay đổi mật khẩu.
- Session phía server, opaque token, cookie cho ứng dụng trình duyệt.
- Opaque bearer token cho client ngoài trình duyệt, dùng cùng cơ chế session.
- Danh sách session, thu hồi từng session và tất cả session.
- EF Core adapter; PostgreSQL là provider được hỗ trợ và kiểm thử đầu tiên.
- Dependency injection, options validation, logging, audit events và email abstraction.
- Endpoint Minimal API có thể bật tắt; ứng dụng cũng gọi service trực tiếp được.
- Tài liệu, sample, CI và các package NuGet đã kiểm thử từ ứng dụng consumer.

### Phạm vi sau v1.0

- Google/Microsoft OIDC, MFA/TOTP, passkey, API key, JWT access token.
- SQL Server/SQLite production adapters, Redis cache, multi-tenancy.
- Không đặt các phần này vào đường găng phát hành v1.0.
- Không xây OAuth/OIDC authorization server trong thư viện này. Nếu cần, đánh giá một sản phẩm chuyên dụng ở kế hoạch riêng.
- Authorization nghiệp vụ, roles/permissions, UI đăng nhập, SMTP provider và hosting do ứng dụng hoặc module riêng đảm nhiệm.

## 2. Khởi tạo project độc lập

Tạo mới toàn bộ project trong thư mục gốc riêng `authkit/`, có thể đặt ở bất kỳ vị trí nào hoặc tách thành repository riêng. Mọi đường dẫn trong kế hoạch tính từ thư mục này. Project có solution, SDK configuration, dependency configuration, tests, samples và CI riêng; có thể sao chép thư mục sang máy khác để restore/build/test/pack. Không cần đọc, di chuyển hoặc tham chiếu mã nguồn của repository chứa bản kế hoạch.

- [x] P01 — Tạo thư mục gốc `authkit/` và solution mới `AuthKit.sln`; tất cả project thuộc solution nằm trong thư mục gốc này. P06–P07 đã thêm bốn library shells và hai sample hosts; A01 bổ sung phần skeleton còn lại.
- [x] P02 — Chốt use cases, consumer mục tiêu và tiêu chí chấp nhận v1 mà không phụ thuộc ứng dụng có sẵn. Deliverable: [phạm vi sản phẩm v1](../authkit/docs/product-scope-v1.md).
- [x] P03 — Định nghĩa hợp đồng public API và các sample mới để chứng minh tích hợp từ đầu. Deliverables: [API contract](../authkit/docs/public-api-v1.md), [sample design](../authkit/docs/sample-design-v1.md); runnable samples thuộc P06.
- [x] P04 — Chọn tên package/namespace sau khi kiểm tra NuGet và repository naming. Prefix `LocalSessions.AuthKit`; repository slug dự kiến `localsessions-authkit`; [bằng chứng và quyết định](../authkit/docs/package-naming.md).
- [x] P05 — Viết ADR về session phía server, target framework, package boundaries và việc tái sử dụng primitive của Microsoft. Deliverables: [ADR 0001](../authkit/docs/adr/0001-runtime-and-package-boundaries.md), [ADR 0002](../authkit/docs/adr/0002-server-side-sessions-and-atomic-store.md), [ADR 0003](../authkit/docs/adr/0003-microsoft-security-primitives.md).
- [x] P06 — Tạo mới sample Minimal API và playground, chỉ tham chiếu các thư viện trong solution độc lập. Hai host chạy được trang chính/liveness; auth/DB integration thuộc H/D/W tasks, chưa triển khai.
- [x] P07 — Đặt mỗi `.csproj` trong thư mục riêng; cấm ProjectReference, linked source, build imports hoặc script tham chiếu đường dẫn bên ngoài project root. Có [boundary guard](../authkit/scripts/Test-ProjectBoundaries.ps1) và [quy tắc](../authkit/docs/project-boundaries.md); build bản copy ngoài repo đã đạt.
- [ ] P08 — Tạo `.gitignore`, `.editorconfig`, `NuGet.Config`, SDK/build/package configuration và CI riêng; không dựa vào cấu hình của thư mục cha.
- [ ] P09 — Cấu hình sample qua environment/user-secrets; cung cấp file cấu hình mẫu và Docker Compose cho PostgreSQL, không hardcode secrets.

Hoàn thành khi solution mới restore/build được từ project root trên môi trường chỉ có SDK phù hợp và quyền truy cập package feed. Build/pack không yêu cầu database, Docker hoặc ứng dụng host đang chạy; integration tests mới yêu cầu Docker/PostgreSQL.

## 3. Tech stack đã chọn

| Thành phần | Quyết định |
| --- | --- |
| Runtime | .NET 10 LTS, target `net10.0`; C# mặc định của SDK, không dùng preview |
| Core | Class library, async API, nullable enabled, `CancellationToken`, `TimeProvider` |
| Web integration | ASP.NET Core 10, `AuthenticationHandler`, policies, Minimal API |
| Password hashing | `PasswordHasher<TUser>` của Microsoft; cấu hình và benchmark work factor, rehash khi cần |
| Session token | 32 byte ngẫu nhiên từ `RandomNumberGenerator`, Base64Url; lưu SHA-256 digest |
| Persistence | EF Core 10 + Npgsql provider tương thích; PostgreSQL |
| Test | xUnit, ASP.NET Core `WebApplicationFactory`, Testcontainers PostgreSQL |
| API contract | DTO có validation, `ProblemDetails`, mã lỗi ổn định |
| Build/release | .NET CLI, NuGet, Source Link, GitHub Actions, SemVer |

Chọn .NET 10 vì là LTS đang được hỗ trợ. Chưa multi-target .NET 8; nếu có consumer bắt buộc dùng bản cũ, cần ADR riêng về thời hạn hỗ trợ và CI matrix. Password hasher là abstraction để có thể thêm Argon2id sau mà vẫn xác minh được hash cũ.

Không tự viết thuật toán mật mã, JWT validator hoặc giao thức OAuth/OIDC. Việc chọn password work factor phải dựa trên hướng dẫn hiện hành và benchmark máy mục tiêu, không sao chép một giá trị mặc định rồi coi là đủ.

## 4. Kiến trúc và cấu trúc thư mục

```text
authkit/                       # Project root độc lập
  AuthKit.sln
  global.json
  Directory.Build.props
  Directory.Packages.props
  NuGet.Config
  .editorconfig
  .gitignore
  README.md
  LICENSE
  compose.yaml
  .github/workflows/
  artifacts/                   # Build/package output, gitignored
  # Các thư mục dưới đây cũng nằm trong authkit/
src/
  AuthKit.Core/                 # Models, contracts, use cases, session/token logic
  AuthKit.AspNetCore/           # Handler, cookies, endpoints, DI, HTTP mapping
  AuthKit.EntityFrameworkCore/  # Entities/configuration/store/transactions
  AuthKit.PostgreSql/           # Npgsql registration và đặc thù provider
tests/
  AuthKit.Core.Tests/
  AuthKit.AspNetCore.Tests/
  AuthKit.PostgreSql.Tests/
  AuthKit.Package.Tests/
samples/
  AuthKit.Playground/
  AuthKit.MinimalApi.PostgreSql/
  AuthKit.Console.PostgreSql/
docs/
  adr/
  security/
plans/
```

Dependency: AspNetCore → Core; EntityFrameworkCore → Core; PostgreSql → EntityFrameworkCore. Core không tham chiếu HTTP, EF Core, Npgsql hoặc host ứng dụng. `PasswordHasher<TUser>` được bọc bằng adapter ở lớp tích hợp; domain sử dụng `IPasswordHasher` riêng.

- [ ] A01 — Tạo projects, references và solution folders đúng sơ đồ dependency.
  P06–P07 đã tạo bốn library shells và hai sample hosts với references đúng hướng; task này còn tests, console sample và kiểm tra skeleton đầy đủ.
- PackageId, AssemblyName và RootNamespace của bốn thư viện theo bảng naming P04; tên project/thư mục giữ như sơ đồ.
- [ ] A02 — Tạo `global.json`, `Directory.Build.props`, central package management và lock files theo chính sách restore đã chọn; giới hạn config discovery ở project root, không kế thừa build/package config của thư mục cha.
- [ ] A03 — Bật nullable, XML docs cho public API, analyzers và cảnh báo nghiêm ngặt phù hợp.
- [ ] A04 — Chốt public types: `AuthUser`, `AuthSession`, `AuthResult<T>`, `AuthError`, các request/response DTO.
- [ ] A05 — Chốt `IAuthService`, `ISessionService`, `IAuthStore`, `IPasswordHasher`, `IAuthEmailSender`, `IAuthAuditSink`.
- [ ] A06 — Thiết kế store theo thao tác nguyên tử của use case, không chỉ repository CRUD hoặc generic transaction callback.
- [ ] A07 — Tạo options cho password, session, verification, cookie, endpoint và rate-limit integration; validate khi startup.
- [ ] A08 — Inject `TimeProvider`; mọi timestamp lưu UTC; định nghĩa chính xác biên hết hạn.
- [ ] A09 — Chốt DI lifetimes, thread safety và hành vi khi gọi trực tiếp từ worker/non-HTTP consumer.
- [ ] A10 — Thêm API baseline để kiểm soát thay đổi public API trước và sau v1.

## 5. Mô hình dữ liệu và tính nhất quán

| Entity | Trường chính và ràng buộc |
| --- | --- |
| User | Id, Email, NormalizedEmail, EmailVerifiedAt, PasswordHash, SecurityVersion, trạng thái, UTC timestamps, concurrency version |
| Session | Id, UserId, TokenHash, SecurityVersion, CreatedAt, LastSeenAt, IdleExpiresAt, AbsoluteExpiresAt, RevokedAt, device metadata |
| ActionToken | Id, UserId, Purpose, TokenHash, ExpiresAt, ConsumedAt, CreatedAt |
| EmailOutbox | Id, loại email, payload bảo vệ phù hợp, CreatedAt, AttemptCount, NextAttemptAt, DeliveredAt |

Device metadata chỉ là thông tin hiển thị; IP/User-Agent không được coi là bằng chứng nhận dạng. Outbox chứa đường link/token gửi email nên phải hạn chế quyền truy cập, không ghi log và xóa payload sau khi gửi hoặc hết hạn.

- [ ] D01 — Chốt ID dạng Guid, giới hạn chiều dài và quy tắc chuẩn hóa email; giữ email gốc để hiển thị.
- [ ] D02 — Thiết kế unique index trên NormalizedEmail và TokenHash; index lookup/cleanup và foreign keys.
- [ ] D03 — Chốt quy tắc xóa user, cascade, retention và cleanup theo từng bảng.
- [ ] D04 — Tạo EF mapping, concurrency token và xử lý unique violation có kiểu thay vì parse chuỗi lỗi.
- [ ] D05 — Cài store cho create user, lookup, create/validate/revoke session và action-token consumption.
- [ ] D06 — Đảm bảo reset password: consume token + update hash + tăng SecurityVersion + revoke sessions trong cùng transaction.
- [ ] D07 — Đảm bảo email verification và token consumption nguyên tử; token sai purpose không thể dùng chéo luồng.
- [ ] D08 — Chốt cập nhật LastSeen có giới hạn tần suất; không kéo dài quá AbsoluteExpiresAt hoặc hồi sinh session revoked.
- [ ] D09 — Tạo migration mẫu và hướng dẫn tích hợp model vào DbContext của consumer; không tự migrate production khi startup.
- [ ] D10 — Thêm PostgreSQL migrations và kiểm tra upgrade trên database có dữ liệu.
- [ ] D11 — Viết shared store contract tests áp dụng cho mọi adapter; memory fake chỉ dùng test/demo.

## 6. Password và các luồng tài khoản

- [ ] U01 — Bọc Microsoft password hasher, xử lý success/failed/rehash-needed; benchmark và tài liệu work factor.
- [ ] U02 — Cho phép passphrase, Unicode, không truncate; có giới hạn độ dài để kiểm soát tài nguyên.
- [ ] U03 — Cài registration: validate, normalize, hash, insert và tạo verification email theo transaction/outbox.
- [ ] U04 — Chốt phản hồi email trùng để tránh enumeration; xử lý race hai request đăng ký cùng email bằng unique constraint.
- [ ] U05 — Cài login với lỗi chung; dùng dummy hash verification khi user không tồn tại để giảm timing khác biệt.
- [ ] U06 — Cài policy tài khoản chưa xác minh email, disabled/locked; không phát session khi policy từ chối.
- [ ] U07 — Rehash sau login thành công nếu cần; cập nhật có concurrency control.
- [ ] U08 — Cài resend verification với cooldown và phản hồi chung; chốt token cũ bị vô hiệu khi phát lại.
- [ ] U09 — Cài confirm email bằng action token, một lần sử dụng, hết hạn và đúng purpose.
- [ ] U10 — Cài forgot password với phản hồi chung cho email tồn tại/không tồn tại, hạn chế gửi email.
- [ ] U11 — Cài reset password nguyên tử; vô hiệu toàn bộ reset token còn lại và sessions; gửi email thông báo.
- [ ] U12 — Cài change password yêu cầu mật khẩu hiện tại; mặc định thu hồi tất cả session, yêu cầu đăng nhập lại.
- [ ] U13 — Cài trạng thái disabled và kiểm tra trạng thái trên mỗi lần xác thực session.
- [ ] U14 — Chốt hành vi retry/idempotency của registration, verify, reset và revoke; ghi rõ việc timeout sau commit.
- [ ] U15 — Giữ email change và account deletion ngoài v1; tài liệu hóa cách host vô hiệu user và cleanup an toàn.

## 7. Session và token

v1 dùng opaque session, không có refresh-token/JWT pair. Token session có thể được truyền bằng cookie hoặc Authorization header, nhưng mỗi endpoint sử dụng scheme được cấu hình rõ ràng.

- [ ] S01 — Tạo token bằng CSPRNG; chỉ trả token raw khi phát hành, không lưu raw trong database/log.
- [ ] S02 — Cài digest lookup, kiểm tra độ dài/format trước truy vấn; dùng comparison phù hợp nếu phải so sánh secret trong bộ nhớ.
- [ ] S03 — Cài idle expiry và absolute expiry; mặc định đề xuất 30 phút idle, 7 ngày absolute, configurable.
- [ ] S04 — Validate session/user/security version mỗi request; không cache v1 để thu hồi có hiệu lực ở request tiếp theo.
- [ ] S05 — Phát token mới sau login; không nhận session identifier do client đề xuất.
- [ ] S06 — List sessions chỉ trả metadata, không trả raw token hoặc digest; luôn scope theo current user.
- [ ] S07 — Revoke current/specific/all sessions; thao tác lặp lại an toàn, không tiết lộ session của user khác.
- [ ] S08 — Chặn session creation nếu password reset/disable đang cạnh tranh; transaction hoặc version recheck phải ngăn session stale được sử dụng.
- [ ] S09 — Cài cleanup theo batch, cancellation và retention; host chủ động bật background worker.
- [ ] S10 — Tài liệu hóa bearer token là secret; client ngoài trình duyệt tự quản lý secure storage.

## 8. ASP.NET Core integration và HTTP contract

API cấu hình dự kiến: `AddAuthKit(...)`, `AddAuthKitPostgreSql(...)`, `AddAuthKitAuthentication(...)`, `MapAuthKitEndpoints(...)`. Thư viện không âm thầm đổi default authentication scheme của host nếu host chưa yêu cầu.

| Endpoint dưới prefix cấu hình | Auth và hành vi |
| --- | --- |
| GET /antiforgery | Browser profile, cấp request token; no-store |
| POST /register | Anonymous, tạo tài khoản/verification |
| POST /login | Anonymous, phát cookie hoặc bearer theo profile cấu hình |
| POST /email/resend | Anonymous, phản hồi chung, rate limit |
| POST /email/confirm | Token một lần trong body |
| POST /password/forgot | Anonymous, phản hồi chung |
| POST /password/reset | Token một lần trong body |
| POST /password/change | Authenticated và mật khẩu hiện tại |
| GET /me | Authenticated, DTO tối thiểu |
| GET /sessions | Authenticated, chỉ session của user hiện tại |
| DELETE /sessions/{id} | Authenticated, thu hồi session thuộc user |
| POST /logout | Thu hồi session hiện tại và xóa cookie |
| POST /logout-all | Authenticated, thu hồi tất cả session |

- [ ] H01 — Cài authentication handlers cho cookie/opaque bearer và tích hợp ClaimsPrincipal.
- [ ] H02 — Chốt scheme names, claim `sub`/NameIdentifier mapping; không gán role từ input client.
- [ ] H03 — Nếu nhiều credential cùng có mặt, dùng policy rõ ràng hoặc từ chối ambiguity; không fallback sang credential khác sau xác thực thất bại.
- [ ] H04 — Cài cookie với HttpOnly, Secure, SameSite=Lax, Path=/; dùng tiền tố `__Host-`, không Domain ở profile mặc định.
- [ ] H05 — Cấu hình cookie development riêng cho HTTP local; fail validation với cấu hình production không an toàn.
- [ ] H06 — Cài ASP.NET Core antiforgery cho thao tác thay đổi trạng thái dùng cookie, gồm login/logout; có cách lấy token cho SPA.
- [ ] H07 — SameSite không thay thế antiforgery; bearer-only endpoint không dựa vào cookie credential.
- [ ] H08 — Map endpoints opt-in, prefix configurable, enable/disable nhóm endpoint, hỗ trợ gọi service từ controller riêng.
- [ ] H09 — Chốt response/status: 400 validation, 401 unauthenticated, 403 forbidden, 429 throttled; dùng mã lỗi ổn định.
- [ ] H10 — Không redirect 401/403 về HTML ở API; không lộ stack trace, DB errors hoặc trạng thái email qua lỗi anonymous.
- [ ] H11 — Validate input, giới hạn body, không bind entity persistence trực tiếp từ request.
- [ ] H12 — Tạo OpenAPI contract và examples cho cookie/bearer; không đưa token thật vào examples.
- [ ] H13 — CORS do host quyết định; cung cấp ví dụ allowlist + credentials, tránh wildcard origin.
- [ ] H14 — Hướng dẫn middleware order, HTTPS, trusted forwarded headers, reverse proxy và path base.
- [ ] H15 — Profile trình duyệt không trả raw token trong JSON; response nhạy cảm dùng Cache-Control: no-store.
- [ ] H16 — Email link đi tới trang host; token được gửi bằng POST để tiêu thụ, tránh GET/email scanner tiêu thụ token.

## 9. Email, rate limiting và observability

- [ ] O01 — Định nghĩa email templates và sender adapter; không buộc consumer dùng dịch vụ SMTP cụ thể.
- [ ] O02 — Base URL cho email được cấu hình/allowlist; không dựng link trực tiếp từ Host header không tin cậy.
- [ ] O03 — Cài outbox dispatcher opt-in, retry có backoff, giới hạn số lần và cảnh báo delivery failure.
- [ ] O04 — Sender dùng idempotency key nếu hỗ trợ; tài liệu hóa email có thể gửi trùng theo at-least-once delivery.
- [ ] O05 — Rate limit login/register/forgot/resend theo IP và account key; account key được hash để giảm lộ PII.
- [ ] O06 — Cung cấp policy ASP.NET Core local và interface host dùng distributed limiter; ghi rõ local limiter không bảo vệ toàn cụm.
- [ ] O07 — Chốt cơ chế backoff/lockout, tránh attacker khóa tài khoản tùy ý; kiểm thử giới hạn trên nhiều instance với adapter host.
- [ ] O08 — Phát audit events cho login, token consumption, password change và session revoke, kèm correlation id.
- [ ] O09 — Log có cấu trúc, không password, raw token, cookie, Authorization header hoặc email link.
- [ ] O10 — Metrics cho auth success/failure, store latency, email delivery, rate limit; tránh labels có cardinality cao/PII.
- [ ] O11 — Chốt fail behavior: store lỗi thì không authenticate; email lỗi retry qua outbox; audit sink lỗi không rollback auth đã commit.
- [ ] O12 — Tài liệu hóa chính sách lưu/xóa IP, User-Agent và audit; redaction trong sample.

## 10. Security review và kiểm thử

- [ ] T01 — Viết threat model: enumeration, credential stuffing, replay, fixation, CSRF, XSS/token theft, race, host-header injection và secret leakage.
- [ ] T02 — Unit test use cases với fake clock/store/email; không dùng sleep cho expiry tests.
- [ ] T03 — Test password sai/đúng, rehash, user không tồn tại, disabled và unverified.
- [ ] T04 — Test email normalization, duplicate registration và concurrent inserts.
- [ ] T05 — Test action token expired, consumed, sai purpose, malformed và hai request tiêu thụ đồng thời: chỉ một thành công.
- [ ] T06 — Test reset/change password đồng thời với login; tất cả session cũ bị vô hiệu, không có auth bằng credential version cũ.
- [ ] T07 — Test session idle/absolute expiry đúng biên, revoke và LastSeen update không hồi sinh session.
- [ ] T08 — Test user A không list/revoke session của user B; không mass assignment claims/id.
- [ ] T09 — Integration test trên PostgreSQL thật với Testcontainers: transactions, unique indexes, concurrency và rollback.
- [ ] T10 — HTTP tests qua WebApplicationFactory: schemes, claims, 401/403, cookie flags, deletion và endpoint options.
- [ ] T11 — Test CSRF cho mọi endpoint cookie thay đổi trạng thái; test cookie/bearer ambiguity và CORS sample.
- [ ] T12 — Test login/reset không lộ thông tin qua status/body; đo timing để tìm chênh lệch đáng kể, không tuyên bố timing tuyệt đối bằng nhau.
- [ ] T13 — Test outbox retry, send failure, duplicate delivery và cleanup token payload.
- [ ] T14 — Test cancellation, dependency unavailable, timeouts và log redaction.
- [ ] T15 — Test migration upgrade từ schema trước trên dữ liệu có sẵn; tài liệu backup/rollback code và schema.
- [ ] T16 — Benchmark login hash và session lookup ở tải dự kiến; ghi môi trường, latency, throughput và giới hạn tài nguyên.
- [ ] T17 — Consumer smoke test dùng package `.nupkg`, không ProjectReference; test Core trong console app và web integration trong sample. Chạy thêm restore/build/test/pack sau khi sao chép project root sang thư mục tạm bên ngoài repository ban đầu để xác nhận không có dependency ẩn.
- [ ] T18 — Dependency vulnerability scan và security review riêng trước v1; xử lý finding hoặc ghi quyết định có lý do.
- [ ] T19 — Test host có sẵn scheme khác, route prefix và custom DbContext; AddAuthKit không phá cấu hình host.

Hoàn thành khi mọi invariant bảo mật có test, integration suite chạy PostgreSQL thật và các lỗi nghiêm trọng được xử lý.

## 11. Documentation và samples

- [ ] W01 — README: mục tiêu, phạm vi, package matrix, supported .NET/DB versions và quickstart.
- [ ] W02 — Sample Minimal API + PostgreSQL: register → gửi email demo → confirm → login → protected endpoint → logout.
- [ ] W03 — Sample browser cookie với antiforgery và sample bearer cho CLI/mobile; tách rõ hai profile.
- [ ] W04 — Hướng dẫn schema/migrations, DI lifetimes, options và email/outbox worker.
- [ ] W05 — Hướng dẫn viết storage/email/password adapters và chạy contract tests.
- [ ] W06 — Hướng dẫn deploy nhiều instance: shared DB, limiter, HTTPS/proxy, cleanup và email worker coordination.
- [ ] W07 — Tài liệu secrets, hashing, token lifecycle, revocation, CSRF và những quyết định host phải cấu hình.
- [ ] W08 — Hướng dẫn clone/copy project độc lập và restore/build/test/pack từ môi trường sạch; liệt kê SDK, package feeds và yêu cầu Docker chỉ cho integration tests.
- [ ] W09 — XML API docs, changelog, contributing, code of conduct và SECURITY.md với kênh báo lỗi bảo mật.
- [ ] W10 — Chọn license và kiểm tra dependency licenses trước khi phát hành.
- [ ] W11 — Troubleshooting: 401/403, cookie không được gửi, antiforgery, DB unavailable và email delivery.

## 12. NuGet, CI và vận hành release

- [ ] R01 — Cấu hình package metadata: id, description, tags, README, license, repository URL và symbols.
- [ ] R02 — Bật deterministic build/Source Link; kiểm tra package không chứa secrets hoặc sample data nhạy cảm.
- [ ] R03 — CI restore locked → build Release → unit/integration tests → pack → consumer smoke test.
- [ ] R04 — Chạy Linux/Windows matrix cho build và tests phù hợp; jobs container đặt trên runner có Docker.
- [ ] R05 — Thêm format/analyzer checks và dependency vulnerability audit; định nghĩa xử lý advisory transitive.
- [ ] R06 — CI fork PR không có quyền publish; release job dùng quyền tối thiểu và cơ chế credential an toàn được NuGet hỗ trợ.
- [ ] R07 — SemVer, API compatibility baseline, release notes và chính sách deprecation.
- [ ] R08 — Phát hành local package trước; sau đó alpha/beta, thử consumer ngoài repo và ghi feedback.
- [ ] R09 — Kiểm tra tên package, ownership, package dependencies và symbol/source links trước publish công khai.
- [ ] R10 — Công bố v1.0 chỉ khi checklist phát hành bên dưới đạt; việc publish là bước thực thi riêng.
- [ ] R11 — Lập quy trình security patch, supported versions, nâng dependency và theo dõi .NET support lifecycle.
- [ ] R12 — Định nghĩa rollback phiên bản package và migration không phá dữ liệu; tránh giả định downgrade schema luôn an toàn.

## 13. Thứ tự triển khai và tiêu chí hoàn thành

| Milestone | Task phụ thuộc | Deliverable và điều kiện hoàn thành |
| --- | --- | --- |
| M0: Chốt thiết kế | P01–P05 | Scope, ADR, public API và threat model bản đầu được ghi rõ |
| M1: Skeleton | M0, P06–P09, A01–A10 | Solution mới build riêng được, samples tạo mới, không tham chiếu ngoài project root |
| M2: Store và core | M1, D01–D11, U01–U15, S01–S10 | Luồng tài khoản/session chạy qua PostgreSQL, tests về atomicity/concurrency đạt |
| M3: Web integration | M2, H01–H16, O01–O12 | HTTP cookie/bearer hoạt động, antiforgery và email delivery có kiểm thử |
| M4: Beta | M3, T01–T19, W01–W11, R01–R09 | Package beta cài vào consumer độc lập được, tài liệu đủ để tích hợp |
| M5: v1.0 | M4, R10–R12 | Security review hoàn tất, public API ổn định, release checklist đạt |

Các task kiểm thử được thực hiện cùng use case tương ứng; M4 là đợt kiểm tra tích hợp và hoàn thiện, không phải lần đầu bắt đầu viết tests. Chưa ấn định lịch vì effort phụ thuộc yêu cầu tương thích, adapter và kết quả security review.

### Checklist bắt buộc trước v1.0

- [ ] Không lưu raw session/action token; outbox payload nhạy cảm có lifecycle và access control rõ ràng.
- [ ] Không có secrets hardcode; không có endpoint demo phát token tùy ý trong package production.
- [ ] Reset/verification token một lần sử dụng được chứng minh bằng concurrent tests.
- [ ] Password reset/disable/revoke có hiệu lực ở request xác thực tiếp theo.
- [ ] Cookie profile có antiforgery, flags an toàn và API không redirect lỗi auth.
- [ ] Tài liệu nêu rõ DB failure, limiter nhiều instance, migration và email failure behavior.
- [ ] Release build, PostgreSQL suite và `.nupkg` consumer smoke test đều đạt.
- [ ] Security findings nghiêm trọng đã xử lý; license, package metadata và ownership đã chốt.
- [ ] Quickstart chạy được từ môi trường sạch; changelog và supported versions đầy đủ.
- [ ] Sao chép riêng project root sang vị trí khác vẫn restore/build/test/pack được, không cần source/config của repository chứa kế hoạch.

### Lệnh xác minh build độc lập

Chạy từ thư mục `authkit/` sau khi đã tạo solution và các project. Lock files được tạo và commit trong giai đoạn skeleton. Integration tests được gắn trait `Category=Integration`; consumer package tests dùng `Category=Package` và chạy sau bước pack.

```powershell
dotnet restore AuthKit.sln --configfile NuGet.Config --locked-mode
dotnet build AuthKit.sln --configuration Release --no-restore
dotnet test AuthKit.sln --configuration Release --no-build --filter "Category!=Integration&Category!=Package"
dotnet pack AuthKit.sln --configuration Release --no-build --output artifacts/packages
dotnet test tests/AuthKit.Package.Tests/AuthKit.Package.Tests.csproj --configuration Release --no-build --filter "Category=Package"
dotnet test AuthKit.sln --configuration Release --no-build --filter "Category=Integration"
```

Chỉ bốn thư viện trong `src/` được đánh dấu `IsPackable=true`; tests và samples đặt `IsPackable=false`. Package tests đọc feed local tại `artifacts/packages` theo project root được truyền rõ ràng. Integration suite dùng Testcontainers khởi tạo PostgreSQL, yêu cầu Docker; Compose dành cho chạy sample thủ công. SDK và NuGet dependencies là điều kiện build, không phải dependency vào source của một ứng dụng khác.

## 14. Backlog sau v1.0

Mỗi nhóm sau cần thiết kế và release riêng, không chỉ thêm endpoint.

- [ ] B01 — OIDC login Google/Microsoft: middleware chính thức, state/nonce/PKCE, callback allowlist và chống account-link takeover.
- [ ] B02 — MFA/TOTP: bảo vệ shared secret, enrollment confirmation, recovery codes hash, step-up và recovery flows.
- [ ] B03 — Passkey/WebAuthn: dùng implementation đã được đánh giá, origin/RP ID validation và credential lifecycle.
- [ ] B04 — API keys: scopes, expiration, hashed storage, rotation, revoke và audit.
- [ ] B05 — JWT module nếu có nhu cầu API phân tán: issuer/audience/algorithm validation, asymmetric keys, JWKS rotation và revocation policy.
- [ ] B06 — Nếu thêm refresh tokens: rotation, token-family reuse detection và atomicity; không áp dụng mô hình refresh cho opaque session v1 một cách máy móc.
- [ ] B07 — SQL Server/SQLite adapters: chạy cùng store contract suite, kiểm tra concurrency đặc thù provider.
- [ ] B08 — Redis caching/distributed limiter: TTL và cache invalidation phải giữ cam kết thu hồi; xác định failure policy.
- [ ] B09 — Multi-tenancy: tenant scope ở mọi lookup/index, tenant-bound tokens và isolation tests.
- [ ] B10 — Authorization module riêng: roles/permissions, tích hợp policies của ASP.NET Core.
- [ ] B11 — Email change/account deletion: reauthentication, xác minh email mới, revoke credentials và retention policy.

## 15. Nguồn kỹ thuật

Kiểm tra ngày 08/10/2026; đối chiếu lại support/package compatibility khi bắt đầu triển khai.

- [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core): căn cứ chọn .NET 10 LTS.
- [ASP.NET Core Identity custom storage providers](https://learn.microsoft.com/aspnet/core/security/authentication/identity-custom-storage-providers): tham khảo ranh giới storage và khả năng mở rộng Identity; kế hoạch này không ép consumer dùng toàn bộ Identity stack.
- [ASP.NET Core antiforgery](https://learn.microsoft.com/aspnet/core/security/anti-request-forgery): cơ chế bảo vệ request dựa trên cookie.

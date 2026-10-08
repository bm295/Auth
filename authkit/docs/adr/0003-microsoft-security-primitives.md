# ADR 0003: Tái sử dụng primitive bảo mật của Microsoft

Ngày: 08/10/2026. Trạng thái: Accepted. Task: P05.

## Quyết định

- Bọc PasswordHasher<TUser> từ Microsoft.Extensions.Identity.Core bằng IPasswordHasher của Core; dùng hash format có version và SuccessRehashNeeded. Chốt work factor qua benchmark U01; không tự viết password KDF.
- Dùng RandomNumberGenerator và SHA256 trong System.Security.Cryptography cho high-entropy token/digest; token hashing không thay thế password hashing.
- ASP.NET integration dựa trên AuthenticationHandler, ClaimsPrincipal, authorization policies, options validation và DI có sẵn.
- Cookie mang raw opaque token, custom handler validate qua store mỗi request; không dùng self-contained cookie ticket thay cho session DB. Dùng CookieOptions chuẩn cho flags/deletion.
- Dùng ASP.NET Core antiforgery cho browser unsafe methods và login/logout; SameSite chỉ là bổ sung. Host chủ động cấu hình scheme, CORS, proxy và HTTPS.
- Không tự xây JWT validator hoặc OAuth/OIDC protocol. Các module sau v1 dùng implementation chính thức/phù hợp ở ADR riêng.

Core không yêu cầu HttpContext hoặc ASP.NET shared framework; Microsoft password primitive là package dependency khi triển khai, chưa thêm vào shell ở P05–P07. Web framework reference chỉ nằm ở web integration/sample projects.

## Hệ quả

Không reimplement toàn bộ ASP.NET Core Identity; consumer sở hữu user model/schema theo adapter contract. Password verification cần tương thích hash cũ khi đổi settings/hasher. Anti-CSRF token cần lấy lại sau identity thay đổi. Authentication scheme không được âm thầm override host defaults.

## Nguồn và xác minh

- [PasswordHasher](https://learn.microsoft.com/en-us/dotnet/api/microsoft.aspnetcore.identity.passwordhasher-1)
- [ASP.NET Core antiforgery](https://learn.microsoft.com/aspnet/core/security/anti-request-forgery)
- [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core)

U01/T03 kiểm tra rehash; H01–H07/T10–T11 kiểm tra session handler/cookie/CSRF. Đây là quyết định kiến trúc, chưa là kết quả security tests.

# Phạm vi sản phẩm và tiêu chí chấp nhận AuthKit v1

Ngày chốt: 08/10/2026. Task: P02. Tài liệu quyết định phạm vi, không tuyên bố các tính năng đã được triển khai.

## Mục tiêu

Cung cấp thư viện NuGet Authentication nhúng vào backend .NET 10, cho phép consumer sở hữu user data, session, database và cấu hình vận hành. Project phải có thể tách thành repository riêng và build từ project root mà không cần source hoặc cấu hình của ứng dụng khác.

Tên đầy đủ là LocalSessions AuthKit, package/namespace dùng prefix `LocalSessions.AuthKit` theo [quyết định P04](package-naming.md). Hợp đồng public API theo [tài liệu P03](public-api-v1.md); các sample được định nghĩa trong [sample design](sample-design-v1.md).

## Consumer mục tiêu

| Consumer | Nhu cầu v1 |
| --- | --- |
| Backend ASP.NET Core phục vụ web/SPA | Email/password, cookie session, antiforgery, endpoints tùy chọn |
| Backend ASP.NET Core phục vụ mobile/CLI | Opaque bearer session, xác thực endpoint và thu hồi session |
| Backend .NET có controller hoặc API riêng | Gọi services trực tiếp, tự ánh xạ HTTP response và UI |
| Worker/console .NET | Gọi core services và adapters qua DI mà không yêu cầu HttpContext |

PostgreSQL là database production được hỗ trợ đầu tiên, thông qua EF Core adapter. UI, email transport, deployment và quyền truy cập nghiệp vụ do consumer quản lý. v1 không dành cho backend ngoài .NET hoặc ứng dụng yêu cầu một OAuth/OIDC authorization server.

## Use cases và tiêu chí chấp nhận

| ID | Use case | Tiêu chí chấp nhận v1 |
| --- | --- | --- |
| UC01 | Đăng ký email/password | Validate và chuẩn hóa email, hash password trước khi lưu; unique email được bảo vệ ở DB kể cả request đồng thời; phản hồi anonymous không tiết lộ email đã tồn tại |
| UC02 | Xác minh email | Token ngẫu nhiên, có purpose và hạn sử dụng; chỉ lưu digest trong action-token store; chỉ một request đồng thời tiêu thụ thành công; chưa xác minh thì không được đăng nhập ở profile mặc định |
| UC03 | Gửi lại email xác minh | Phản hồi chung, cooldown/rate limit; token cũ bị vô hiệu khi phát token mới; gửi email qua sender abstraction/outbox |
| UC04 | Đăng nhập | Credential hợp lệ và user active/verified mới tạo session; lỗi anonymous chung; hash được nâng cấp khi cần; phát token mới, không chấp nhận identifier do client đề xuất |
| UC05 | Xác thực request | Cookie hoặc opaque bearer theo profile rõ ràng; kiểm tra user, security version, revoke, idle và absolute expiry; DB lỗi không xác thực thành công; không fallback credential sau thất bại |
| UC06 | Xem tài khoản hiện tại | Chỉ trả DTO được cho phép, không password hash, token digest hoặc dữ liệu nội bộ |
| UC07 | Xem và thu hồi session | User chỉ xem/thu hồi session của mình; token và digest không xuất hiện trong danh sách; revoke có hiệu lực ở request xác thực tiếp theo |
| UC08 | Đăng xuất | Thu hồi session hiện tại, xóa cookie đúng thuộc tính nếu dùng cookie; thao tác lặp lại an toàn |
| UC09 | Đăng xuất tất cả | Thu hồi tất cả session của user; không ảnh hưởng session của user khác |
| UC10 | Quên và đặt lại mật khẩu | Forgot phản hồi chung; reset token đúng purpose, chưa hết hạn, một lần sử dụng; consume token, đổi hash, tăng security version và revoke sessions nguyên tử; vô hiệu các reset token còn lại |
| UC11 | Đổi mật khẩu | Yêu cầu xác thực và mật khẩu hiện tại; cập nhật nguyên tử; thu hồi toàn bộ session và yêu cầu đăng nhập lại |
| UC12 | Vô hiệu tài khoản | Host có thể disable user qua service được cung cấp; session bị từ chối ở request xác thực tiếp theo, kể cả khi disable cạnh tranh với login |
| UC13 | Tích hợp email | Host cung cấp sender; link dùng base URL cấu hình; outbox hỗ trợ retry, token payload nhạy cảm không bị log và được xóa khi gửi hoặc hết hạn |
| UC14 | Tích hợp backend | Endpoints opt-in, prefix configurable; host gọi service trực tiếp được; không âm thầm thay default authentication scheme |
| UC15 | Dọn dữ liệu hết hạn | Host bật worker chủ động; cleanup theo batch, hỗ trợ cancellation và retention; không làm session hết hạn hoạt động lại |

## Quy tắc sản phẩm bắt buộc

- v1 dùng opaque server-side session; không có JWT access/refresh token pair.
- Browser profile dùng cookie HttpOnly/Secure, SameSite và antiforgery cho request thay đổi trạng thái, gồm login/logout. Không trả raw session token trong JSON ở profile này.
- Bearer profile dành cho client quản lý secret storage; không tự xác thực bằng cookie khi bearer thất bại.
- Password dùng implementation của Microsoft qua abstraction; work factor được benchmark và có cơ chế rehash. Không tự viết thuật toán mật mã.
- Raw session/action token không lưu ở bảng credential hoặc ghi log. Email outbox chứa secret để gửi phải có bảo vệ, quyền truy cập và vòng đời xóa được tài liệu hóa.
- Trạng thái reset, disable và revoke được kiểm tra qua DB trên mỗi lần xác thực; v1 không cache kết quả xác thực.
- Rate limiting có profile local và điểm mở rộng cho distributed limiter; local limiter không được mô tả là bảo vệ toàn cụm.
- API dùng mã lỗi ổn định, phản hồi 401/403 phù hợp; không redirect API sang HTML và không lộ lỗi DB/stack trace.
- Authorization nghiệp vụ dựa trên policies của host; không nhận roles/claims đặc quyền từ input client.

## Tiêu chí nghiệm thu phát hành v1

| ID | Bằng chứng cần có |
| --- | --- |
| AC01 | Project root có solution/config/CI riêng; sao chép sang vị trí độc lập vẫn restore/build/pack được bằng SDK và package feeds đã tài liệu hóa |
| AC02 | Build/pack không cần DB, Docker hoặc host chạy; integration tests nêu riêng yêu cầu Docker/PostgreSQL |
| AC03 | Core không tham chiếu HTTP, EF Core, PostgreSQL hoặc project ứng dụng; mọi ProjectReference nằm trong project root |
| AC04 | UC01–UC15 có kiểm thử theo hành vi, gồm PostgreSQL integration tests cho unique constraints, transaction và concurrent token consumption |
| AC05 | HTTP tests chứng minh cookie flags, antiforgery, schemes, 401/403 và user/session isolation; reset/login race không cho phép sử dụng credential version cũ |
| AC06 | Consumer ngoài solution cài `.nupkg` từ local feed và tích hợp được; có console consumer cho core và ASP.NET Core consumer cho web integration |
| AC07 | Quickstart từ môi trường sạch chạy được register → verify → login → protected endpoint → logout; hướng dẫn cả cookie và bearer profile |
| AC08 | Threat model và security review hoàn tất; không còn finding nghiêm trọng chưa xử lý; logs không chứa passwords, raw tokens hoặc sensitive headers |
| AC09 | Có hướng dẫn migration, options, adapter contracts, email failure, retention, multiple instances, proxy/HTTPS và secret management |
| AC10 | Package metadata/license/support policy/changelog đầy đủ; release CI build, test, pack và consumer smoke test đạt |

Các tiêu chí trên là điều kiện nghiệm thu chức năng và phát hành, chưa phải kết quả kiểm thử. Ngưỡng hiệu năng được xác lập trong task benchmark theo môi trường và tải mục tiêu trước beta.

## Ngoài phạm vi v1

OAuth/OIDC login, MFA/TOTP, passkey, API keys, JWT, refresh tokens, SQL Server/SQLite production support, Redis cache, multi-tenancy, roles/permissions module, email change và account deletion thuộc backlog sau v1. UI đăng nhập, SMTP implementation và hạ tầng hosting không thuộc deliverable thư viện v1.

## Điều kiện thay đổi phạm vi

Thay đổi consumer/runtime/database/protocol hoặc đưa một tính năng backlog vào v1 phải cập nhật tài liệu này, task plan và tiêu chí nghiệm thu tương ứng. Không suy ra yêu cầu từ một ứng dụng có sẵn.

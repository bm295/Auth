# Thiết kế samples v1

Task P03. P06 đã tạo hai host chạy được tại AuthKit.MinimalApi.PostgreSql và AuthKit.Playground, cùng library shells để tham chiếu nội bộ. Hosts hiện chỉ có trang chính/liveness; chưa có auth/database integration. Các luồng đầy đủ bên dưới thuộc H/D/W tasks, chưa được coi là hoàn thành.

## Sample matrix

| Sample | Cấu trúc và consumer | Bằng chứng |
| --- | --- | --- |
| AuthKit.MinimalApi.PostgreSql | ASP.NET Core net10, PostgreSQL, endpoint browser `/auth/browser` và bearer `/auth/bearer` | UC01–UC11, opt-in endpoints, explicit schemes, DB migrations và không lẫn credential transport |
| AuthKit.Playground | Web app mới, UI nhỏ gọi browser profile, email capture development-only | Cookie/antiforgery, account/session UI, verify/reset bằng POST, log redaction |
| AuthKit.Console.PostgreSql | Console net10 dùng Core/PostgreSql và DI, không AspNetCore | Core services chạy không HttpContext; custom sender, token wrapper và cancellation |
| Package consumer fixtures | Temporary console/web projects ngoài solution, PackageReference từ local artifacts feed | Cài `.nupkg` và chạy smoke tests không ProjectReference hoặc source ngoài package |

Sample projects không pack; source và project references nằm trong project root. Console consumer thêm vào A01/W05 để đáp ứng AC06, package fixtures tạo bởi T17. Playground là UI minh họa, không phải UI library production.

## Luồng browser

1. Host cấu hình DB connection, PublicBaseUri HTTPS, sender và cookie scheme; chạy migrations chủ động.
2. Client GET `/auth/browser/antiforgery`; nhận token và cookie, đính header đã cấu hình vào unsafe requests.
3. POST register; nhận accepted chung. Email đi vào development inbox riêng, không được ghi raw token vào console logs.
4. UI đọc email link trong development inbox, gửi token qua POST confirm; GET link không tự consume token.
5. POST login; nhận user/session metadata, browser nhận HttpOnly cookie. Không có raw session token trong response JSON hoặc UI.
6. Lấy lại antiforgery token sau login, GET protected endpoint và `/sessions`.
7. Thử revoke session khác, change/reset password và kiểm tra request xác thực tiếp theo bị từ chối.
8. POST logout; kiểm tra cookie xóa và protected endpoint trả 401.

Development inbox chỉ bật trong Development, loopback/local access, dữ liệu trong bộ nhớ và tự hết hạn; không endpoint công khai ở production. Sample không hỗ trợ chạy production với sender/config dev.

## Luồng bearer

1. Register/verify theo bearer endpoint profile; POST login nhận session token một lần.
2. Client giữ token trong memory cho demo, gửi Authorization: Bearer tới protected endpoints.
3. List/revoke/logout-all, xác nhận token không còn xác thực ở request tiếp theo.
4. Kiểm tra cookie trên request bearer không thay thế bearer bị sai; không lưu token vào browser localStorage trong sample.

## Luồng console và package consumers

- Console tạo ServiceCollection, đăng ký Core, store, password hasher và sender; resolve services trong scope, gửi CancellationToken.
- Dùng inbox development để verify user rồi gọi login/validate/list/revoke trực tiếp, không HttpContext.
- Package smoke tests pack bốn packages, dựng local feed, tạo consumer từ templates trong thư mục tạm và chạy restore/build/use-case tối thiểu.
- Consumer compile từ public APIs và runtime dependencies của package; không tham chiếu assembly output hoặc source trong src.

## Checklist hoàn thành samples

- [ ] Cả browser/bearer đều có request examples, setup/config và hướng dẫn migration.
- [ ] Demo chạy từ môi trường sạch; SDK đủ để build, Docker chỉ cần khi chạy PostgreSQL/integration.
- [ ] UI/HTTP DTO không hiển thị password hash/digest hoặc raw browser token.
- [ ] Các luồng rejected credentials, invalid action token, expiry, revoke, dependency failure và CSRF có kiểm thử phù hợp.
- [ ] Sample schemas/config cùng public API docs; không hardcode secrets hoặc dùng default production credentials.
- [ ] Console chạy không web runtime; package consumers xác nhận installation từ `.nupkg`.

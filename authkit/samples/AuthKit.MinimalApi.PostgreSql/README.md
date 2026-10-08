# Minimal API + PostgreSQL sample

P06 tạo host mới và references tới AspNetCore/PostgreSql trong solution. Hiện host chỉ có `/` và `/health/live`; chưa kết nối DB, chưa có endpoints auth, credentials hoặc protected routes. Không giả lập đăng nhập thành công.

Từ project root, dùng .NET 10 SDK:

```powershell
dotnet run --project samples/AuthKit.MinimalApi.PostgreSql -- --urls http://127.0.0.1:5081
```

GET `http://127.0.0.1:5081/` trả trạng thái scaffold; `/health/live` chỉ xác nhận process đang chạy, không xác nhận DB/auth readiness. Profile HTTP loopback này dành cho host scaffold; browser cookie integration sau này dùng HTTPS.

Khi H01–H16/D05 hoàn tất, host đăng ký services/store, host-controlled email sender và map browser `/auth/browser` + bearer `/auth/bearer` riêng. P09 bổ sung environment/user-secrets, config mẫu và PostgreSQL Compose; W02/T10–T11 bổ sung use-case demo và tests. Xem [thiết kế samples](../../docs/sample-design-v1.md).

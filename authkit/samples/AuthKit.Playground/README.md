# Playground sample

Web host và trang tĩnh được tạo mới cho P06, tham chiếu AspNetCore/PostgreSql trong project root. Hiện chỉ có landing page và `/health/live`; chưa có auth UI, database hoặc development email inbox.

Từ project root:

```powershell
dotnet run --project samples/AuthKit.Playground -- --urls http://127.0.0.1:5082
```

Mở `http://127.0.0.1:5082/`. HTTP loopback chỉ dành cho scaffold; cookie auth sẽ dùng HTTPS khi tích hợp. Các luồng registration/verification/login/session và email capture được nối ở H/W tasks theo [sample design](../../docs/sample-design-v1.md). Không có login giả, token demo hoặc credential hardcode.

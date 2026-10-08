# LocalSessions AuthKit

Thư viện Authentication C# dành cho backend .NET, đóng gói NuGet và tích hợp trực tiếp vào ứng dụng consumer.

Project được khởi tạo mới, có solution riêng tại `AuthKit.sln`. Mọi project được thêm sau này phải nằm trong thư mục gốc này; không tham chiếu source hoặc project bên ngoài.

## Trạng thái

Đã hoàn thành P01–P07: thiết kế, ADR, project boundaries và hai sample host mới. Solution có bốn library shells và hai web samples, build riêng được. Các shell chưa có auth services hoặc database implementation; samples chạy trang chính/liveness, chưa thực hiện đăng nhập.

## Phạm vi sản phẩm

Xem [use cases và tiêu chí chấp nhận v1](docs/product-scope-v1.md). Tài liệu này nằm trong project root để có thể mang theo khi tách project thành repository riêng.

- [Public API v1](docs/public-api-v1.md)
- [Thiết kế samples v1](docs/sample-design-v1.md)
- [Package và namespace naming](docs/package-naming.md): prefix `LocalSessions.AuthKit`, repository slug dự kiến `localsessions-authkit`.
- ADR: [runtime và packages](docs/adr/0001-runtime-and-package-boundaries.md), [session và atomic store](docs/adr/0002-server-side-sessions-and-atomic-store.md), [Microsoft primitives](docs/adr/0003-microsoft-security-primitives.md).
- [Project boundaries](docs/project-boundaries.md)

## Kiểm tra solution

Từ thư mục gốc AuthKit, dùng .NET 10 SDK:

```powershell
dotnet sln AuthKit.sln list
dotnet build AuthKit.sln --configuration Release
powershell -NoProfile -File scripts/Test-ProjectBoundaries.ps1
```

## Chạy sample hosts

```powershell
dotnet run --project samples/AuthKit.MinimalApi.PostgreSql -- --urls http://127.0.0.1:5081
dotnet run --project samples/AuthKit.Playground -- --urls http://127.0.0.1:5082
```

Chạy mỗi lệnh ở một terminal riêng. Mở `/` và `/health/live` tại cổng tương ứng. Không cần DB/Docker để build hoặc chạy scaffold hiện tại. Xem README trong từng sample để biết phần tích hợp còn chờ triển khai.

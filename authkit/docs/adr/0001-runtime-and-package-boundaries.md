# ADR 0001: Runtime và package boundaries

Ngày: 08/10/2026. Trạng thái: Accepted. Task: P05.

## Quyết định

Target .NET 10 LTS (`net10.0`), phiên bản C# mặc định của SDK, nullable enabled, không preview hoặc multi-target v1. Mọi project nằm trong project root độc lập.

| Package | Trách nhiệm | Project dependencies |
| --- | --- | --- |
| LocalSessions.AuthKit.Core | Domain, contracts, use cases, storage/password/email abstractions; Microsoft password-hasher adapter không yêu cầu HTTP | Không có |
| LocalSessions.AuthKit.AspNetCore | Handlers, cookies, antiforgery, endpoints, HTTP DTO, DI web integration | Core |
| LocalSessions.AuthKit.EntityFrameworkCore | Mapping, atomic stores, transactions, outbox persistence | Core |
| LocalSessions.AuthKit.PostgreSql | Npgsql registration, provider-specific concurrency/exception mapping | EntityFrameworkCore |

Core không tham chiếu ASP.NET Core framework, EF hoặc Npgsql. Core có thể dùng Microsoft.Extensions cho DI/options và Identity.Extensions cho password hashing khi triển khai. Consumer không phải dùng toàn bộ ASP.NET Core Identity user/store schema. Samples là consumer, không cung cấp implementation mà thư viện phụ thuộc vào.

PackageId, AssemblyName và RootNamespace theo P04. Mỗi csproj ở thư mục riêng; không linked source, external ProjectReference hoặc build imports tới source ngoài project root. SDK/NuGet là dependencies được khai báo, không phải external source. Không dùng cấu hình hoặc source của ứng dụng chứa thư mục checkout.

## Lý do và hệ quả

.NET 10 LTS tạo baseline mới thống nhất. Tách web/storage khỏi core cho phép dùng services trong console/worker và thay adapter. Không hỗ trợ net8 trong v1 làm giảm compatibility matrix; yêu cầu tương thích cũ phải có quyết định riêng.

P05–P07 tạo các project shell đủ build và reference đúng hướng. A01 bổ sung tests/console/solution folders còn thiếu; A02/P08 bổ sung SDK pin, central dependencies và build/CI config. Shell chưa có public services hoặc auth implementation.

## Xác minh

Build solution Release; chạy script kiểm tra project boundaries; build lại sau khi copy project root sang vị trí khác. Khi có dependencies thật, dùng architecture checks và consumer package tests theo T17/T19.

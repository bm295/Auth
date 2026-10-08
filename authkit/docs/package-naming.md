# Package, namespace và repository naming

Ngày quyết định: 08/10/2026. Task: P04.

## Quyết định

Tên đầy đủ: **LocalSessions AuthKit**. Prefix package và namespace: `LocalSessions.AuthKit`. Tên ngắn trong tài liệu có thể tiếp tục dùng AuthKit. Không phát hành package tên trần `AuthKit`.

Repository slug khi tạo repository riêng: `localsessions-authkit`. Thư mục checkout có thể mang tên bất kỳ; giữ `authkit/` và `AuthKit.sln` hiện tại vì không ảnh hưởng package identity. Chưa tạo repository remote hoặc đăng ký NuGet ownership trong task này.

| Project/thư mục trong src | PackageId, AssemblyName, RootNamespace |
| --- | --- |
| AuthKit.Core | LocalSessions.AuthKit.Core |
| AuthKit.AspNetCore | LocalSessions.AuthKit.AspNetCore |
| AuthKit.EntityFrameworkCore | LocalSessions.AuthKit.EntityFrameworkCore |
| AuthKit.PostgreSql | LocalSessions.AuthKit.PostgreSql |

Public types ở namespace tương ứng hoặc namespace con như `.Contracts`, `.Options`, `.DependencyInjection`. Extension methods nằm trong namespace `.DependencyInjection` của package sở hữu để consumer import rõ ràng. Tests/samples giữ tên project trong kế hoạch và không publish package.

Không có umbrella package ở v1. Core không phụ thuộc web/EF; AspNetCore và EntityFrameworkCore phụ thuộc Core; PostgreSql phụ thuộc EntityFrameworkCore. Consumer web PostgreSQL cài AspNetCore và PostgreSql, nhận các dependency còn lại qua NuGet.

## Bằng chứng kiểm tra

Kiểm tra trực tiếp NuGet V3 flat-container bằng HTTP GET ngày 08/10/2026:

| ID viết thường | HTTP | Kết luận |
| --- | --- | --- |
| authkit | 200 | Có phiên bản 8.1.0, 8.5.0, 8.6.0, 8.6.4; không dùng tên trần |
| authkit.core / authkit.aspnetcore / authkit.entityframeworkcore / authkit.postgresql | 404 từng ID | Không thấy version index, nhưng tên gốc đã có sản phẩm khác |
| localsessions.authkit.core | 404 | Không thấy version index |
| localsessions.authkit.aspnetcore | 404 | Không thấy version index |
| localsessions.authkit.entityframeworkcore | 404 | Không thấy version index |
| localsessions.authkit.postgresql | 404 | Không thấy version index |

Endpoint mẫu: `https://api.nuget.org/v3-flatcontainer/localsessions.authkit.core/index.json`. HTTP 404 chỉ chứng minh không tìm thấy version index lúc kiểm tra, không chứng minh prefix chưa reserved hoặc đảm bảo quyền publish.

Search web với `"LocalSessions.AuthKit"` và `site.github.com "localsessions-authkit"` không trả kết quả lúc kiểm tra. Đây là kiểm tra tên có thể tìm thấy công khai, không phải xác nhận khả dụng repository tại một tài khoản GitHub cụ thể.

Các tên AuthKit hiện có gồm [NuGet AuthKit](https://www.nuget.org/packages/AuthKit), [Azos.AuthKit](https://www.nuget.org/packages/Azos.AuthKit), [WorkOS AuthKit](https://github.com/workos/authkit) và [.NET AuthKit.Server](https://github.com/AuthKits/AuthKit.Server). Prefix riêng giúp phân biệt package của project này.

## Trước phát hành

R09 kiểm tra lại tất cả package IDs, prefix reservation, account ownership và repository URL thật. Theo [NuGet prefix reservation](https://learn.microsoft.com/en-us/nuget/nuget-org/id-prefix-reservation), việc không có package không đồng nghĩa có quyền sử dụng prefix. Nếu publish bị từ chối, đổi prefix đồng bộ trước v1; không tự suy ra ownership từ tên tài khoản/máy phát triển.

P04 chốt naming dùng để triển khai; chưa giữ chỗ, publish hoặc chứng nhận quyền sở hữu tên.

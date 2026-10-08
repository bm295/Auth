# Ranh giới project độc lập

Task P07. Mỗi project có csproj trong thư mục riêng dưới `src/` hoặc `samples/`; tests sau này nằm dưới `tests/`. Solution chỉ chứa project bên trong project root.

Dependency graph:

```text
Core
  ↑ AspNetCore
  ↑ EntityFrameworkCore ← PostgreSql

MinimalApi.PostgreSql → AspNetCore + PostgreSql
Playground           → AspNetCore + PostgreSql
```

Không cho phép ProjectReference ra ngoài root, linked source, HintPath tới assembly ngoài root hoặc explicit build imports ra ngoài root. SDK/NuGet references là dependencies của toolchain; không copy source ngoài vào build. Script/build config bổ sung sau này phải dùng đường dẫn tính từ project root/PSScriptRoot, không từ repository cha hoặc user-specific absolute paths.

Từ project root:

```powershell
pwsh -File scripts/Test-ProjectBoundaries.ps1
dotnet build AuthKit.sln --configuration Release
```

Nếu chỉ có Windows PowerShell, chạy `powershell -File scripts/Test-ProjectBoundaries.ps1`. Script kiểm tra csproj, solution references, linked source và explicit source/build paths; paths động/wildcard trong các mục này bị từ chối để tránh kiểm tra nhầm. NuGet package/framework references không bị coi là source paths. P08/R03 tích hợp guard vào CI.

Guard là kiểm tra cấu trúc source, không thay thế phân tích MSBuild đã evaluate hoặc sandbox chống mã build độc hại. Build config/imports mới và scripts phải review; SDK pin và chống kế thừa config thư mục cha thuộc P08/A02. Xác minh copy/build ở vị trí riêng bảo vệ khỏi phụ thuộc vô tình vào checkout hiện tại.

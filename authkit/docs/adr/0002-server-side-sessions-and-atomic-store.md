# ADR 0002: Server-side session và atomic store

Ngày: 08/10/2026. Trạng thái: Accepted. Task: P05.

## Quyết định

v1 dùng opaque token 32 byte từ CSPRNG, Base64Url encoding; chỉ lưu SHA-256 digest trong session/action-token store. Không JWT/refresh pair. Cookie browser và bearer client là hai transport của cùng session model, có profile/routes riêng.

Mỗi request xác thực phải đọc session/user từ database, kiểm tra revoked, disabled, verified policy, security version, idle expiry và absolute expiry. Không cache auth v1. Thời gian UTC qua TimeProvider; LastSeen update được throttle và không vượt absolute expiry hoặc khôi phục session revoked.

PostgreSQL là provider đầu tiên; IAuthStore biểu diễn thao tác nguyên tử thay vì generic CRUD/transaction delegate. EF adapters sở hữu transactions, concurrency và provider errors; core sở hữu policies/use-case orchestration.

## Transaction invariants

- Create user + verification token + email outbox commit cùng nhau; unique normalized email bảo vệ duplicate/race.
- Verification consume theo token digest/purpose/unexpired/unconsumed và verify user trong cùng transaction; chỉ một concurrent consumer thành công.
- Reset consume token + đổi password + tăng security version + vô hiệu action tokens còn lại + revoke sessions + email outbox trong cùng transaction.
- Change password recheck current hash/version, cập nhật password/version và revoke sessions nguyên tử.
- Disable tăng security version và revoke sessions nguyên tử; session lookup vẫn kiểm tra user disabled.
- Login verify password snapshot rồi conditional create session theo expected security version/hash và active/verified state. Sau reset/disable commit, session stale không xác thực được, kể cả insert cạnh tranh.
- Session touch conditional theo active/unexpired/current version, không ghi đè revoked state.
- Outbox worker claim có lease/ownership, complete/retry kiểm tra lease; email delivery at-least-once, dùng idempotency key khi sender hỗ trợ.

Token dùng một lần không bị consume bởi GET/email scanner; host UI gửi POST. Payload outbox cần raw action token để gửi, là ngoại lệ lưu secret phục vụ delivery: bảo vệ bằng cơ chế host-managed key, kiểm soát access, không log, xóa payload sau delivered/expired; digest vẫn dùng để validate. D03/O03 quyết định schema và key lifecycle cụ thể trước triển khai.

## Lý do và hệ quả

DB lookup mỗi request cho phép revoke có hiệu lực ở lần xác thực tiếp theo, đổi lại latency và phụ thuộc DB. Không hủy ngược request đã authenticate. Nếu DB lỗi, không authenticate; HTTP mapping thành 503 sanitized thay vì giả credential sai.

Redis/cache/JWT chỉ thêm sau nếu có ADR về revocation semantics. Memory fake chỉ dùng test, không là production fallback.

## Xác minh

PostgreSQL integration tests cho duplicate email, double consume, reset/login/disable races, rollback và revoke/touch races; expiry tests dùng fake clock. Store adapter khác phải chạy cùng contract suite.

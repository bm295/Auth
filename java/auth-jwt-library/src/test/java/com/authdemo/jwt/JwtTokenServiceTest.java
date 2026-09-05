package com.authdemo.jwt;

import static org.junit.jupiter.api.Assertions.*;
import java.time.Instant;
import java.util.Map;
import org.junit.jupiter.api.Test;

class JwtTokenServiceTest {
  private final JwtTokenService tokens = new JwtTokenService("ThisIsADemoJwtSigningKey1234567890!", "AuthDemoIssuer", "AuthDemoAudience");
  @Test void createsAndValidatesToken() {
    String token = tokens.createToken("manager@contoso.demo", Map.of("tenant_id", "contoso"), Instant.now().plusSeconds(60));
    JwtPrincipal principal = tokens.validate(token);
    assertEquals("manager@contoso.demo", principal.subject());
    assertEquals("contoso", principal.requiredStringClaim("tenant_id"));
  }
  @Test void rejectsTamperedToken() {
    String token = tokens.createToken("user", Map.of(), Instant.now().plusSeconds(60));
    assertThrows(JwtValidationException.class, () -> tokens.validate(token.substring(0, token.length() - 1) + "x"));
  }
}

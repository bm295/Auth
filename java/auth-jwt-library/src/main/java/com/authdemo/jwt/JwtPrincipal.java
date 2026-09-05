package com.authdemo.jwt;

import java.util.Map;

/** A verified JWT identity and its claims. */
public record JwtPrincipal(String subject, Map<String, Object> claims) {
  public JwtPrincipal {
    claims = Map.copyOf(claims);
  }

  public String requiredStringClaim(String name) {
    Object value = claims.get(name);
    if (!(value instanceof String string) || string.isBlank()) {
      throw new JwtValidationException("JWT is missing required claim: " + name);
    }
    return string;
  }
}

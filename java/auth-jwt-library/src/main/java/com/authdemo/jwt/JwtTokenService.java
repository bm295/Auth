package com.authdemo.jwt;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Clock;
import java.time.Instant;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

/** Creates and validates HS256 JWTs using the Auth repository's issuer/audience contract. */
public final class JwtTokenService {
  private static final Base64.Encoder ENCODER = Base64.getUrlEncoder().withoutPadding();
  private static final Base64.Decoder DECODER = Base64.getUrlDecoder();
  private static final ObjectMapper JSON = new ObjectMapper();
  private final byte[] secret;
  private final String issuer;
  private final String audience;
  private final Clock clock;

  public JwtTokenService(String secret, String issuer, String audience) {
    this(secret, issuer, audience, Clock.systemUTC());
  }

  JwtTokenService(String secret, String issuer, String audience, Clock clock) {
    if (secret == null || secret.getBytes(StandardCharsets.UTF_8).length < 32) {
      throw new IllegalArgumentException("JWT HS256 secret must be at least 32 bytes.");
    }
    this.secret = secret.getBytes(StandardCharsets.UTF_8);
    this.issuer = requireValue(issuer, "issuer");
    this.audience = requireValue(audience, "audience");
    this.clock = clock;
  }

  public String createToken(String subject, Map<String, ?> additionalClaims, Instant expiresAt) {
    if (expiresAt == null || !expiresAt.isAfter(clock.instant())) throw new IllegalArgumentException("Expiry must be in the future.");
    Map<String, Object> payload = new LinkedHashMap<>();
    if (additionalClaims != null) payload.putAll(additionalClaims);
    payload.put("iss", issuer); payload.put("aud", audience); payload.put("sub", requireValue(subject, "subject"));
    payload.put("iat", clock.instant().getEpochSecond()); payload.put("exp", expiresAt.getEpochSecond());
    try {
      String header = encodeJson(Map.of("alg", "HS256", "typ", "JWT"));
      String body = encodeJson(payload);
      String unsigned = header + "." + body;
      return unsigned + "." + ENCODER.encodeToString(hmac(unsigned));
    } catch (Exception e) { throw new IllegalStateException("Unable to create JWT.", e); }
  }

  public JwtPrincipal validate(String token) {
    try {
      String[] parts = token == null ? new String[0] : token.split("\\.", -1);
      if (parts.length != 3) throw new JwtValidationException("JWT must contain three sections.");
      Map<String, Object> header = decodeJson(parts[0]);
      if (!"HS256".equals(header.get("alg"))) throw new JwtValidationException("JWT must use HS256.");
      if (!MessageDigest.isEqual(hmac(parts[0] + "." + parts[1]), DECODER.decode(parts[2]))) throw new JwtValidationException("JWT signature is invalid.");
      Map<String, Object> claims = decodeJson(parts[1]);
      if (!issuer.equals(claims.get("iss")) || !audience.equals(claims.get("aud"))) throw new JwtValidationException("JWT issuer or audience is invalid.");
      if (!(claims.get("sub") instanceof String subject) || subject.isBlank()) throw new JwtValidationException("JWT subject is invalid.");
      if (!(claims.get("exp") instanceof Number exp) || exp.longValue() <= clock.instant().getEpochSecond()) throw new JwtValidationException("JWT has expired.");
      return new JwtPrincipal(subject, claims);
    } catch (JwtValidationException e) { throw e;
    } catch (Exception e) { throw new JwtValidationException("JWT is malformed.", e); }
  }

  private byte[] hmac(String value) throws Exception {
    Mac mac = Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec(secret, "HmacSHA256"));
    return mac.doFinal(value.getBytes(StandardCharsets.US_ASCII));
  }
  private static String encodeJson(Object value) throws Exception { return ENCODER.encodeToString(JSON.writeValueAsBytes(value)); }
  private static Map<String, Object> decodeJson(String value) throws Exception { return JSON.readValue(DECODER.decode(value), new TypeReference<>() {}); }
  private static String requireValue(String value, String name) { if (value == null || value.isBlank()) throw new IllegalArgumentException(name + " is required."); return value; }
}

package com.authdemo.jwt;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfSystemProperty;

@EnabledIfSystemProperty(named = "auth.demo.url", matches = "http://127\\.0\\.0\\.1:[0-9]+")
class JwtInteropTest {
  private static final ObjectMapper JSON = new ObjectMapper();
  private static final String DEMO_KEY = "ThisIsADemoJwtSigningKey1234567890!";
  private static final Base64.Encoder ENCODER = Base64.getUrlEncoder().withoutPadding();
  private static final Base64.Decoder DECODER = Base64.getUrlDecoder();
  private final JwtTokenService javaValidator =
      new JwtTokenService(DEMO_KEY, "AuthDemoIssuer", "AuthDemoAudience");
  private final HttpClient http =
      HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(3)).build();
  private final String url = System.getProperty("auth.demo.url");

  @Test
  void acceptsTokenMintedByDotnet() throws Exception {
    String token = fetchToken();
    assertEquals(200, protectedStatus(token));
    JwtPrincipal principal = javaValidator.validate(token);
    assertEquals("manager@contoso.demo", principal.subject());
    assertEquals("contoso", principal.requiredStringClaim("tenant_id"));
  }

  @Test
  void rejectsTamperedSignature() throws Exception {
    String[] parts = fetchToken().split("\\.");
    byte[] signature = DECODER.decode(parts[2]);
    signature[0] ^= 1;
    assertRejected(parts[0] + "." + parts[1] + "." + ENCODER.encodeToString(signature),
        "tampered signature");
  }

  @Test
  void rejectsWrongIssuer() throws Exception {
    assertRejected(withClaim(fetchToken(), "iss", "other-issuer"), "wrong issuer");
  }

  @Test
  void rejectsWrongAudience() throws Exception {
    assertRejected(withClaim(fetchToken(), "aud", "other-audience"), "wrong audience");
  }

  @Test
  void rejectsExpiredToken() throws Exception {
    assertRejected(withClaim(fetchToken(), "exp", Instant.now().minusSeconds(60).getEpochSecond()),
        "expired token");
  }

  @Test
  @EnabledIfSystemProperty(named = "auth.demo.cases", matches = ".+")
  void rejectsAgentRegressionCases() throws Exception {
    JsonNode cases = JSON.readTree(Path.of(System.getProperty("auth.demo.cases")).toFile());
    String token = fetchToken();
    for (JsonNode item : cases) {
      String claim = item.required("claim").asText();
      assertRejected(withClaim(token, claim, item.required("value").asText()), "extra " + claim);
    }
  }

  private String fetchToken() throws Exception {
    HttpResponse<String> response = http.send(request("/auth/jwt/token").build(),
        HttpResponse.BodyHandlers.ofString());
    assertEquals(200, response.statusCode(), "demo token endpoint");
    return JSON.readTree(response.body()).required("token").asText();
  }

  private int protectedStatus(String token) throws Exception {
    return http.send(request("/demo/protected/jwt").header("Authorization", "Bearer " + token).build(),
        HttpResponse.BodyHandlers.discarding()).statusCode();
  }

  private HttpRequest.Builder request(String path) {
    return HttpRequest.newBuilder(URI.create(url + path)).timeout(Duration.ofSeconds(5));
  }

  private void assertRejected(String token, String scenario) throws Exception {
    assertEquals(401, protectedStatus(token), ".NET must reject " + scenario);
    assertThrows(JwtValidationException.class, () -> javaValidator.validate(token),
        "Java must reject " + scenario);
  }

  private static String withClaim(String token, String claim, Object value) throws Exception {
    String[] parts = token.split("\\.");
    ObjectNode payload = (ObjectNode) JSON.readTree(DECODER.decode(parts[1]));
    payload.set(claim, JSON.valueToTree(value));
    String unsigned = parts[0] + "." + ENCODER.encodeToString(JSON.writeValueAsBytes(payload));
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(DEMO_KEY.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
    return unsigned + "." + ENCODER.encodeToString(mac.doFinal(unsigned.getBytes(StandardCharsets.US_ASCII)));
  }
}

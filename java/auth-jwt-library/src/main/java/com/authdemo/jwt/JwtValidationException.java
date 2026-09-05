package com.authdemo.jwt;

/** Indicates that a bearer token cannot be trusted. */
public final class JwtValidationException extends SecurityException {
  public JwtValidationException(String message) { super(message); }
  public JwtValidationException(String message, Throwable cause) { super(message, cause); }
}

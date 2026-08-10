package com.agentforge.backend.auth.exception;

public class RefreshTokenReuseException
        extends RuntimeException {

    public RefreshTokenReuseException(String message) {
        super(message);
    }
}
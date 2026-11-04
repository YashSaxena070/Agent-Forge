package com.agentforge.backend.domain.mfa;

public enum MfaType {
    TOTP("totp", "Time-based One-Time Password"),
    WEBAUTHN("webauthn", "WebAuthn / Passkeys"),
    BACKUP_CODES("backup_codes", "Backup Codes"),
    SMS("sms", "SMS"),
    EMAIL("email", "Email");

    private final String code;
    private final String description;

    MfaType(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() { return code; }
    public String getDescription() { return description; }
}
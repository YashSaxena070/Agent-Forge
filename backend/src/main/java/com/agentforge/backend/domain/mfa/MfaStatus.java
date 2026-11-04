package com.agentforge.backend.domain.mfa;

public enum MfaStatus {
    PENDING_SETUP("pending_setup", "Pending setup"),
    ACTIVE("active", "Active"),
    INACTIVE("inactive", "Inactive"),
    LOCKED("locked", "Locked"),
    EXPIRED("expired", "Expired");

    private final String code;
    private final String description;

    MfaStatus(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() { return code; }
    public String getDescription() { return description; }
}
package com.agentforge.backend.tenant;

public enum MemberRole {
    OWNER("owner"),
    ADMIN("admin"),
    DEVELOPER("developer"),
    VIEWER("viewer"),
    OPERATOR("operator"),
    SECURITY("security"),
    BILLING("billing");

    private final String code;

    MemberRole(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    public boolean canInvite() {
        return this == OWNER || this == ADMIN;
    }

    public boolean canRemoveMembers() {
        return this == OWNER || this == ADMIN;
    }
}

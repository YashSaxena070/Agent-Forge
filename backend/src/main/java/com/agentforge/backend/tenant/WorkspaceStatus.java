package com.agentforge.backend.tenant;

public enum WorkspaceStatus {
    ACTIVE("active"),
    SUSPENDED("suspended"),
    DELETED("deleted"),
    TRIAL("trial");

    private final String code;

    WorkspaceStatus(String code) {
        this.code = code;
    }

    public String getCode() { return code; }
}
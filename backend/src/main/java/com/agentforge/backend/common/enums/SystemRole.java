package com.agentforge.backend.common.enums;

import java.util.List;

public enum SystemRole {
    USER,
    SUPER_ADMIN;

    public List<String> getPermissions() {
        if (this == SUPER_ADMIN) {
            return List.of("ADMIN", "USER");
        }
        return List.of("USER");
    }
}

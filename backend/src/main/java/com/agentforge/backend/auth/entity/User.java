package com.agentforge.backend.auth.entity;

import java.time.LocalDateTime;
import java.util.UUID;

public class User {
    UUID id;

    String fullName;

    String email;

    String password;

    Boolean enabled;

    Boolean emailVerified;

    LocalDateTime createdAt;

    LocalDateTime updatedAt;
}

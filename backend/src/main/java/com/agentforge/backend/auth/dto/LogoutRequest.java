package com.agentforge.backend.auth.dto;

import lombok.Getter;
import lombok.Setter;


public record LogoutRequest(String refreshToken) {
}

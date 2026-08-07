package com.agentforge.backend.common.exception;

import lombok.Builder;

import java.time.LocalDateTime;
import java.util.Map;

@Builder
public record ErrorResponse(

        boolean success,

        int status,

        String error,

        String message,

        String path,

        LocalDateTime timestamp,

        Map<String, String> validationErrors

) {
}
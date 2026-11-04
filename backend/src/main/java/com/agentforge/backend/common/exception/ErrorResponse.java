package com.agentforge.backend.common.exception;

import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.Map;

@Getter
@Builder(toBuilder = true)
public class ErrorResponse {

    private final boolean success;
    private final int status;
    private final String error;
    private final String message;
    private final String path;
    private final java.time.LocalDateTime timestamp;
    private final Map<String, String> validationErrors;

}
package com.agentforge.backend.common.exception;

import com.agentforge.backend.auth.exception.EmailAlreadyExistsException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(EmailAlreadyExistsException.class)
    public ResponseEntity<ErrorResponse> handleEmailExists(

            EmailAlreadyExistsException exception,

            HttpServletRequest request

    ) {

        ErrorResponse response = ErrorResponse.builder()

                .success(false)

                .status(HttpStatus.CONFLICT.value())

                .error("Conflict")

                .message(exception.getMessage())

                .path(request.getRequestURI())

                .timestamp(LocalDateTime.now())

                .build();

        return ResponseEntity.status(HttpStatus.CONFLICT)

                .body(response);

    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(

            MethodArgumentNotValidException exception,

            HttpServletRequest request

    ) {

        Map<String, String> errors = new HashMap<>();

        for (FieldError error : exception.getBindingResult().getFieldErrors()) {

            errors.put(

                    error.getField(),

                    error.getDefaultMessage()

            );

        }

        ErrorResponse response = ErrorResponse.builder()

                .success(false)

                .status(HttpStatus.BAD_REQUEST.value())

                .error("Validation Failed")

                .message("Validation failed.")

                .path(request.getRequestURI())

                .validationErrors(errors)

                .timestamp(LocalDateTime.now())

                .build();

        return ResponseEntity.badRequest()

                .body(response);

    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneric(

            Exception exception,

            HttpServletRequest request

    ) {

        ErrorResponse response = ErrorResponse.builder()

                .success(false)

                .status(HttpStatus.INTERNAL_SERVER_ERROR.value())

                .error("Internal Server Error")

                .message(exception.getMessage())

                .path(request.getRequestURI())

                .timestamp(LocalDateTime.now())

                .build();

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)

                .body(response);

    }

}
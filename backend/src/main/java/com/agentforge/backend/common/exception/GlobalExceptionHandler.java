package com.agentforge.backend.common.exception;

import com.agentforge.backend.auth.exception.EmailAlreadyExistsException;
import com.agentforge.backend.auth.exception.InvalidRefreshTokenException;
import com.agentforge.backend.auth.exception.RefreshTokenReuseException;
import com.agentforge.backend.organization.exception.*;
import com.agentforge.backend.project.exception.ProjectNotFoundException;
import com.agentforge.backend.project.exception.ProjectSlugAlreadyExistsException;
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

    @ExceptionHandler(InvalidRefreshTokenException.class)
    public ResponseEntity<ErrorResponse> handleInvalidRefreshToken(

            InvalidRefreshTokenException exception,

            HttpServletRequest request

    ) {

        ErrorResponse response =
                ErrorResponse.builder()

                        .success(false)

                        .status(
                                HttpStatus.UNAUTHORIZED.value()
                        )

                        .error("Unauthorized")

                        .message(exception.getMessage())

                        .path(request.getRequestURI())

                        .timestamp(
                                LocalDateTime.now()
                        )

                        .build();

        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(response);
    }

    @ExceptionHandler(RefreshTokenReuseException.class)
    public ResponseEntity<ErrorResponse> handleRefreshTokenReuse(

            RefreshTokenReuseException exception,

            HttpServletRequest request

    ) {

        ErrorResponse response =
                ErrorResponse.builder()

                        .success(false)

                        .status(
                                HttpStatus.UNAUTHORIZED.value()
                        )

                        .error("Unauthorized")

                        .message(
                                "Refresh token is no longer valid."
                        )

                        .path(request.getRequestURI())

                        .timestamp(
                                LocalDateTime.now()
                        )

                        .build();

        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(response);
    }

    @ExceptionHandler(OrganizationNotFoundException.class)
    public ResponseEntity<ErrorResponse>
    handleOrganizationNotFound(
            OrganizationNotFoundException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(HttpStatus.NOT_FOUND.value())
                        .error("Not Found")
                        .message(exception.getMessage())
                        .path(request.getRequestURI())
                        .timestamp(LocalDateTime.now())
                        .build();

        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(response);
    }

    @ExceptionHandler(
            OrganizationAccessDeniedException.class
    )
    public ResponseEntity<ErrorResponse>
    handleOrganizationAccessDenied(
            OrganizationAccessDeniedException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(HttpStatus.FORBIDDEN.value())
                        .error("Forbidden")
                        .message(exception.getMessage())
                        .path(request.getRequestURI())
                        .timestamp(LocalDateTime.now())
                        .build();

        return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(response);
    }

    @ExceptionHandler(
            InvitationNotFoundException.class
    )
    public ResponseEntity<ErrorResponse>
    handleInvitationNotFound(
            InvitationNotFoundException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(HttpStatus.NOT_FOUND.value())
                        .error("Not Found")
                        .message(exception.getMessage())
                        .path(request.getRequestURI())
                        .timestamp(LocalDateTime.now())
                        .build();

        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(response);
    }

    @ExceptionHandler(
            InvalidInvitationException.class
    )
    public ResponseEntity<ErrorResponse>
    handleInvalidInvitation(
            InvalidInvitationException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(HttpStatus.BAD_REQUEST.value())
                        .error("Bad Request")
                        .message(exception.getMessage())
                        .path(request.getRequestURI())
                        .timestamp(LocalDateTime.now())
                        .build();

        return ResponseEntity
                .badRequest()
                .body(response);
    }

    @ExceptionHandler(
            MemberAlreadyExistsException.class
    )
    public ResponseEntity<ErrorResponse>
    handleMemberAlreadyExists(
            MemberAlreadyExistsException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(HttpStatus.CONFLICT.value())
                        .error("Conflict")
                        .message(exception.getMessage())
                        .path(request.getRequestURI())
                        .timestamp(LocalDateTime.now())
                        .build();

        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(response);
    }

    @ExceptionHandler(ProjectNotFoundException.class)
    public ResponseEntity<ErrorResponse>
    handleProjectNotFound(
            ProjectNotFoundException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(
                                HttpStatus.NOT_FOUND.value()
                        )
                        .error("Not Found")
                        .message(
                                exception.getMessage()
                        )
                        .path(
                                request.getRequestURI()
                        )
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build();

        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(response);
    }

    @ExceptionHandler(
            ProjectSlugAlreadyExistsException.class
    )
    public ResponseEntity<ErrorResponse>
    handleProjectSlugExists(
            ProjectSlugAlreadyExistsException exception,
            HttpServletRequest request
    ) {

        ErrorResponse response =
                ErrorResponse.builder()
                        .success(false)
                        .status(
                                HttpStatus.CONFLICT.value()
                        )
                        .error("Conflict")
                        .message(
                                exception.getMessage()
                        )
                        .path(
                                request.getRequestURI()
                        )
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build();

        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(response);
    }



}
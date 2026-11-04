package com.agentforge.backend.mfa;

import com.agentforge.backend.auth.dto.*;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.mfa.MfaService.TotpSetupResponse;
import com.agentforge.backend.mfa.MfaService.TotpVerifyResponse;
import com.agentforge.backend.mfa.MfaService.WebAuthnRegistrationStart;
import com.agentforge.backend.mfa.MfaService.WebAuthnAuthenticationStart;
import com.agentforge.backend.mfa.MfaService.BackupCodesResponse;
import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.security.auth.CustomUserDetails;
import com.yubico.webauthn.data.AuthenticatorAssertionResponse;
import com.yubico.webauthn.data.AuthenticatorAttestationResponse;
import com.yubico.webauthn.data.PublicKeyCredentialCreationOptions;
import com.yubico.webauthn.data.PublicKeyCredentialRequestOptions;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.LocalDateTime;
import java.util.UUID;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/v1/mfa")
@RequiredArgsConstructor
public class MfaController {

    private final MfaService mfaService;

    @PostMapping("/totp/setup")
    public ResponseEntity<ApiResponse<TotpSetupResponse>> setupTotp(
            Authentication authentication,
            @RequestBody @Valid TotpSetupRequest request
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        TotpSetupResponse response = mfaService.setupTotp(user, request.deviceName());

        return ResponseEntity.ok(ApiResponse.success("TOTP setup initiated", response));
    }

    @PostMapping("/totp/verify-setup")
    public ResponseEntity<ApiResponse<TotpVerifyResponse>> verifyTotpSetup(
            Authentication authentication,
            @RequestBody @Valid TotpVerifySetupRequest request
    ) {
        boolean valid = mfaService.verifyTotpSetup(request.methodId(), request.code());
        
        return ResponseEntity.ok(ApiResponse.success(
                valid ? "TOTP verified successfully" : "Invalid code",
                new TotpVerifyResponse(valid, valid ? "TOTP enabled" : "Invalid code")
        ));
    }

    @PostMapping("/totp/verify")
    public ResponseEntity<ApiResponse<TotpVerifyResponse>> verifyTotp(
            Authentication authentication,
            @RequestBody @Valid TotpVerifyRequest request
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        boolean valid = mfaService.verifyTotp(user, request.code());

        return ResponseEntity.ok(ApiResponse.success(
                valid ? "TOTP verified" : "Invalid code",
                new TotpVerifyResponse(valid, valid ? "Verified" : "Invalid code")
        ));
    }

    @PostMapping("/webauthn/register/start")
    public ResponseEntity<ApiResponse<WebAuthnRegistrationStart>> startWebAuthnRegistration(
            Authentication authentication,
            @RequestBody @Valid WebAuthnRegisterStartRequest request
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        var response = mfaService.startWebAuthnRegistration(user, request.deviceName());

        return ResponseEntity.ok(ApiResponse.success("WebAuthn registration started", response));
    }

    @PostMapping("/webauthn/register/finish")
    public ResponseEntity<ApiResponse<TotpVerifyResponse>> finishWebAuthnRegistration(
            Authentication authentication,
            @RequestBody @Valid WebAuthnRegisterFinishRequest request
    ) {
        boolean valid = mfaService.finishWebAuthnRegistration(request.methodId(), request.response());

        return ResponseEntity.ok(ApiResponse.success(
                valid ? "Security key registered" : "Registration failed",
                new TotpVerifyResponse(valid, valid ? "Security key registered" : "Registration failed")
        ));
    }

    @PostMapping("/webauthn/authenticate/start")
    public ResponseEntity<ApiResponse<com.agentforge.backend.mfa.MfaService.WebAuthnAuthenticationStart>> startWebAuthnAuthentication(
            Authentication authentication
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        var response = mfaService.startWebAuthnAuthentication(user);

        return ResponseEntity.ok(ApiResponse.success("WebAuthn authentication started", response));
    }

    @PostMapping("/webauthn/authenticate/finish")
    public ResponseEntity<ApiResponse<TotpVerifyResponse>> finishWebAuthnAuthentication(
            Authentication authentication,
            @RequestBody @Valid WebAuthnAuthFinishRequest request
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        boolean valid = mfaService.finishWebAuthnAuthentication(user, request.response());

        return ResponseEntity.ok(ApiResponse.success(
                valid ? "WebAuthn verified" : "Verification failed",
                new TotpVerifyResponse(valid, valid ? "Verified" : "Invalid credential")
        ));
    }

    @PostMapping("/backup-codes/generate")
    public ResponseEntity<ApiResponse<BackupCodesResponse>> generateBackupCodes(
            Authentication authentication
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        BackupCodesResponse response = mfaService.generateBackupCodes(user);

        return ResponseEntity.ok(ApiResponse.success("Backup codes generated", response));
    }

    @PostMapping("/backup-codes/verify")
    public ResponseEntity<ApiResponse<TotpVerifyResponse>> verifyBackupCode(
            Authentication authentication,
            @RequestBody @Valid BackupCodeVerifyRequest request
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        boolean valid = mfaService.verifyBackupCode(user, request.code());

        return ResponseEntity.ok(ApiResponse.success(
                valid ? "Backup code accepted" : "Invalid backup code",
                new TotpVerifyResponse(valid, valid ? "Verified" : "Invalid backup code")
        ));
    }

    @GetMapping("/methods")
    public ResponseEntity<ApiResponse<List<MfaMethodResponse>>> getMethods(
            Authentication authentication
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        List<MfaMethodResponse> methods = mfaService.getActiveMethods(user).stream()
                .map(m -> new MfaMethodResponse(
                        m.getId(),
                        m.getMethodType().name(),
                        m.getName(),
                        m.getStatus().name(),
                        m.getVerifiedAt(),
                        m.getLastUsedAt()
                ))
                .toList();

        return ResponseEntity.ok(ApiResponse.success("MFA methods retrieved", methods));
    }

    @DeleteMapping("/methods/{methodId}")
    public ResponseEntity<ApiResponse<Void>> disableMfa(
            Authentication authentication,
            @PathVariable UUID methodId
    ) {
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();
        User user = userDetails.getUser();

        mfaService.disableMfa(user, com.agentforge.backend.domain.mfa.MfaType.valueOf(
                mfaService.getActiveMethods(user).stream()
                        .filter(m -> m.getId().equals(methodId))
                        .findFirst()
                        .map(m -> m.getMethodType().name())
                        .orElseThrow()
        ));

        return ResponseEntity.ok(ApiResponse.success("MFA method disabled", null));
    }

    // DTOs
    public record TotpSetupRequest(@NotBlank String deviceName) {}
    public record TotpVerifySetupRequest(UUID methodId, @NotBlank @Size(min = 6, max = 6) String code) {}
    public record TotpVerifyRequest(@NotBlank @Size(min = 6, max = 6) String code) {}
    public record TotpVerifyResponse(boolean valid, String message) {}

    public record WebAuthnRegisterStartRequest(@NotBlank String deviceName) {}
    public record WebAuthnRegisterFinishRequest(UUID methodId, @Valid AuthenticatorAttestationResponse response) {}
    public record WebAuthnAuthFinishRequest(@Valid AuthenticatorAssertionResponse response) {}

    public record BackupCodeVerifyRequest(@NotBlank @Size(min = 8, max = 8) String code) {}

    public record MfaMethodResponse(
            UUID id,
            String type,
            String name,
            String status,
            LocalDateTime verifiedAt,
            LocalDateTime lastUsedAt
    ) {}
}
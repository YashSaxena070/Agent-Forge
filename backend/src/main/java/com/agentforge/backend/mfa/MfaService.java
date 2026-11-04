package com.agentforge.backend.mfa;

import com.agentforge.backend.domain.mfa.MfaMethod;
import com.agentforge.backend.domain.mfa.MfaStatus;
import com.agentforge.backend.domain.mfa.MfaType;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.mfa.MfaMethodRepository;
import com.agentforge.backend.common.util.CryptoUtil;
import com.warrenstrange.googleauth.GoogleAuthenticator;
import com.warrenstrange.googleauth.GoogleAuthenticatorKey;
import com.warrenstrange.googleauth.GoogleAuthenticatorQRGenerator;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;
import com.yubico.webauthn.data.AuthenticatorAssertionResponse;
import com.yubico.webauthn.data.AuthenticatorAttestationResponse;
import com.yubico.webauthn.data.PublicKeyCredentialCreationOptions;
import com.yubico.webauthn.data.PublicKeyCredentialRequestOptions;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class MfaService {

    private final MfaMethodRepository mfaRepository;
    private final CryptoUtil cryptoUtil;

    @Value("${mfa.totp.issuer:AgentForge}")
    private String totpIssuer;

    @Value("${mfa.max-failed-attempts:5}")
    private int maxFailedAttempts;

    @Value("${mfa.lockout-minutes:15}")
    private int lockoutMinutes;

    private final GoogleAuthenticator googleAuthenticator = new GoogleAuthenticator();

    @jakarta.annotation.PostConstruct
    public void init() {
        cryptoUtil.initialize(getEncryptionKey());
    }

    private String getEncryptionKey() {
        return System.getenv().getOrDefault("ENCRYPTION_KEY",
                "your-32-byte-base64-encryption-key==");
    }

    // ========== TOTP ==========

    public TotpSetupResponse setupTotp(User user, String deviceName) {
        Optional<MfaMethod> existing = mfaRepository.findByUserAndMethodTypeAndStatus(
                user, MfaType.TOTP, MfaStatus.ACTIVE);
        if (existing.isPresent()) {
            throw new IllegalStateException("TOTP already configured");
        }

        GoogleAuthenticatorKey key = googleAuthenticator.createCredentials();
        String secret = key.getKey();
        String qrCodeUrl = GoogleAuthenticatorQRGenerator.getOtpAuthURL(totpIssuer, user.getEmail(), key);

        MfaMethod method = new MfaMethod();
        method.setUser(user);
        method.setMethodType(MfaType.TOTP);
        method.setName(deviceName != null ? deviceName : "Authenticator App");
        method.setStatus(MfaStatus.PENDING_SETUP);
        method.setSecret(secret);
        mfaRepository.save(method);

        return new TotpSetupResponse(secret, qrCodeUrl, method.getId());
    }

    public boolean verifyTotpSetup(UUID methodId, String code) {
        MfaMethod method = mfaRepository.findById(methodId)
                .orElseThrow(() -> new IllegalArgumentException("MFA method not found"));

        if (method.getStatus() != MfaStatus.PENDING_SETUP) {
            throw new IllegalStateException("MFA method not in setup state");
        }

        String secret = method.getSecret();
        if (secret == null) {
            throw new IllegalStateException("Secret not found");
        }

        boolean valid = googleAuthenticator.authorize(secret, Integer.parseInt(code));
        if (valid) {
            method.setStatus(MfaStatus.ACTIVE);
            method.setVerifiedAt(LocalDateTime.now());
            mfaRepository.save(method);
        } else {
            method.incrementFailedAttempts(3, 15);
            mfaRepository.save(method);
        }
        return valid;
    }

    public boolean verifyTotp(User user, String code) {
        List<MfaMethod> methods = mfaRepository.findAllByUserAndMethodTypeAndStatus(
                user, MfaType.TOTP, MfaStatus.ACTIVE);

        for (MfaMethod method : methods) {
            if (isLocked(method)) continue;

            String secret = method.getSecret();
            if (secret != null && googleAuthenticator.authorize(secret, Integer.parseInt(code))) {
                method.markUsed();
                method.resetFailedAttempts();
                mfaRepository.save(method);
                return true;
            } else {
                method.incrementFailedAttempts(maxFailedAttempts, lockoutMinutes);
                mfaRepository.save(method);
            }
        }
        return false;
    }

    // ========== Backup Codes ==========

    public BackupCodesResponse generateBackupCodes(User user) {
        List<String> codes = new ArrayList<>();
        Random random = new Random();
        for (int i = 0; i < 10; i++) {
            codes.add(String.format("%08d", random.nextInt(100_000_000)));
        }

        Optional<MfaMethod> existing = mfaRepository.findByUserAndMethodTypeAndStatus(
                user, MfaType.BACKUP_CODES, MfaStatus.ACTIVE);

        MfaMethod method = existing.orElseGet(() -> {
            MfaMethod m = new MfaMethod();
            m.setUser(user);
            m.setMethodType(MfaType.BACKUP_CODES);
            m.setName("Backup Codes");
            m.setStatus(MfaStatus.ACTIVE);
            return m;
        });

        method.addBackupCodes(codes);
        mfaRepository.save(method);

        return new BackupCodesResponse(codes);
    }

    public boolean verifyBackupCode(User user, String code) {
        List<MfaMethod> methods = mfaRepository.findAllByUserAndMethodTypeAndStatus(
                user, MfaType.BACKUP_CODES, MfaStatus.ACTIVE);

        for (MfaMethod method : methods) {
            if (method.verifyBackupCode(code)) {
                mfaRepository.save(method);
                return true;
            }
        }
        return false;
    }

    // ========== Management ==========

    @Transactional
    public void disableMfa(User user, MfaType type) {
        mfaRepository.findByUserAndMethodTypeAndStatus(user, type, MfaStatus.ACTIVE)
                .ifPresent(method -> {
                    method.setStatus(MfaStatus.INACTIVE);
                    mfaRepository.save(method);
                });
    }

    @Transactional
    public void disableAllMfa(User user) {
        List<MfaMethod> methods = mfaRepository.findByUserAndStatus(user, MfaStatus.ACTIVE);
        methods.forEach(m -> m.setStatus(MfaStatus.INACTIVE));
        mfaRepository.saveAll(methods);
    }

    public List<MfaMethod> getActiveMethods(User user) {
        return mfaRepository.findByUserAndStatus(user, MfaStatus.ACTIVE);
    }

    public List<MfaMethod> getAllMethods(User user) {
        return mfaRepository.findByUser(user);
    }

    private boolean isLocked(MfaMethod method) {
        return method.getStatus() == MfaStatus.LOCKED
                && method.getLockedUntil() != null
                && method.getLockedUntil().isAfter(LocalDateTime.now());
    }


    // ========== WebAuthn ==========

    public WebAuthnRegistrationStart startWebAuthnRegistration(User user, String deviceName) {
        MfaMethod method = new MfaMethod();
        method.setUser(user);
        method.setMethodType(MfaType.WEBAUTHN);
        method.setName(deviceName != null ? deviceName : "Security Key");
        method.setStatus(MfaStatus.PENDING_SETUP);
        mfaRepository.save(method);

        return new WebAuthnRegistrationStart(method.getId(), null);
    }

    public boolean finishWebAuthnRegistration(UUID methodId, AuthenticatorAttestationResponse response) {
        Optional<MfaMethod> methodOpt = mfaRepository.findById(methodId);
        if (methodOpt.isEmpty()) {
            return false;
        }
        MfaMethod method = methodOpt.get();
        method.setStatus(MfaStatus.ACTIVE);
        method.setVerifiedAt(LocalDateTime.now());
        mfaRepository.save(method);
        return true;
    }

    public WebAuthnAuthenticationStart startWebAuthnAuthentication(User user) {
        return new WebAuthnAuthenticationStart(null, null);
    }

    public boolean finishWebAuthnAuthentication(User user, AuthenticatorAssertionResponse response) {
        List<MfaMethod> methods = mfaRepository.findAllByUserAndMethodTypeAndStatus(user, MfaType.WEBAUTHN, MfaStatus.ACTIVE);
        if (methods.isEmpty()) {
            return false;
        }
        MfaMethod method = methods.get(0);
        method.markUsed();
        mfaRepository.save(method);
        return true;
    }

    // Response DTOs
    public record TotpSetupResponse(String secret, String qrCodeUrl, UUID methodId) {}
    public record TotpVerifyResponse(boolean valid, String message) {}
    public record BackupCodesResponse(List<String> codes) {}
    public record WebAuthnRegistrationStart(UUID methodId, PublicKeyCredentialCreationOptions options) {
        public WebAuthnRegistrationStart(UUID methodId) {
            this(methodId, null);
        }
    }
    public record WebAuthnAuthenticationStart(UUID methodId, PublicKeyCredentialRequestOptions options) {
        public WebAuthnAuthenticationStart(PublicKeyCredentialRequestOptions options) {
            this(null, options);
        }
    }
}
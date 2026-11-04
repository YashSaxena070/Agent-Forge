package com.agentforge.backend.domain.mfa;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.common.util.CryptoUtil;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "mfa_methods",
        uniqueConstraints = {
                @UniqueConstraint(columnNames = {"user_id", "method_type", "name"})
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class MfaMethod extends BaseEntity {

    @Id
    @GeneratedValue
    @Column(name = "id", columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private com.agentforge.backend.domain.user.User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "method_type", nullable = false, length = 20)
    private MfaType methodType;

    @Column(name = "name", nullable = false, length = 100)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false, length = 20)
    private MfaStatus status;

    @Column(name = "secret_encrypted", columnDefinition = "TEXT")
    private String secretEncrypted;

    @Column(name = "secret_iv", length = 64)
    private String secretIv;

    @Column(name = "backup_codes", columnDefinition = "jsonb")
    private String backupCodesJson;

    @Column(name = "used_backup_codes", columnDefinition = "jsonb")
    private String usedBackupCodesJson;

    @Column(name = "credential_id", length = 255, unique = true)
    private String credentialId;

    @Column(name = "public_key", columnDefinition = "TEXT")
    private String publicKey;

    @Column(name = "sign_count")
    private long signCount = 0;

    @Column(name = "aaguid", length = 36)
    private String aaguid;

    @Column(name = "contact_value", length = 255)
    private String contactValue;

    @Column(name = "verified_at")
    private LocalDateTime verifiedAt;

    @Column(name = "last_used_at")
    private LocalDateTime lastUsedAt;

    @Column(name = "failed_attempts")
    private int failedAttempts = 0;

    @Column(name = "locked_until")
    private LocalDateTime lockedUntil;

    // Explicit getters and setters for Lombok compatibility
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public com.agentforge.backend.domain.user.User getUser() { return user; }
    public void setUser(com.agentforge.backend.domain.user.User user) { this.user = user; }

    public MfaType getMethodType() { return methodType; }
    public void setMethodType(MfaType methodType) { this.methodType = methodType; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public MfaStatus getStatus() { return status; }
    public void setStatus(MfaStatus status) { this.status = status; }

    public String getSecretEncrypted() { return secretEncrypted; }
    public void setSecretEncrypted(String secretEncrypted) { this.secretEncrypted = secretEncrypted; }

    public String getSecretIv() { return secretIv; }
    public void setSecretIv(String secretIv) { this.secretIv = secretIv; }

    public String getBackupCodesJson() { return backupCodesJson; }
    public void setBackupCodesJson(String backupCodesJson) { this.backupCodesJson = backupCodesJson; }

    public String getUsedBackupCodesJson() { return usedBackupCodesJson; }
    public void setUsedBackupCodesJson(String usedBackupCodesJson) { this.usedBackupCodesJson = usedBackupCodesJson; }

    public String getCredentialId() { return credentialId; }
    public void setCredentialId(String credentialId) { this.credentialId = credentialId; }

    public String getPublicKey() { return publicKey; }
    public void setPublicKey(String publicKey) { this.publicKey = publicKey; }

    public long getSignCount() { return signCount; }
    public void setSignCount(long signCount) { this.signCount = signCount; }

    public String getAaguid() { return aaguid; }
    public void setAaguid(String aaguid) { this.aaguid = aaguid; }

    public String getContactValue() { return contactValue; }
    public void setContactValue(String contactValue) { this.contactValue = contactValue; }

    public LocalDateTime getVerifiedAt() { return verifiedAt; }
    public void setVerifiedAt(LocalDateTime verifiedAt) { this.verifiedAt = verifiedAt; }

    public LocalDateTime getLastUsedAt() { return lastUsedAt; }
    public void setLastUsedAt(LocalDateTime lastUsedAt) { this.lastUsedAt = lastUsedAt; }

    public int getFailedAttempts() { return failedAttempts; }
    public void setFailedAttempts(int failedAttempts) { this.failedAttempts = failedAttempts; }

    public LocalDateTime getLockedUntil() { return lockedUntil; }
    public void setLockedUntil(LocalDateTime lockedUntil) { this.lockedUntil = lockedUntil; }

    public String getSecret() {
        if (secretEncrypted == null) return null;

        try {
            var crypto = CryptoUtil.getInstance();
            return crypto.decrypt(secretEncrypted, secretIv).orElse(null);
        } catch (Exception e) {
            return null;
        }
    }

    public void setSecret(String secret) {
        try {
            var crypto = CryptoUtil.getInstance();
            var result = crypto.encrypt(secret);
            this.secretEncrypted = result.encrypted();
            this.secretIv = result.iv();
        } catch (Exception e) {
            throw new IllegalStateException("Failed to encrypt secret", e);
        }
    }

    public void addBackupCodes(List<String> codes) {
        try {
            var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            var arrayNode = mapper.createArrayNode();
            for (String code : codes) {
                arrayNode.add(code);
            }
            this.backupCodesJson = mapper.writeValueAsString(arrayNode);
            this.usedBackupCodesJson = mapper.writeValueAsString(List.of());
        } catch (Exception e) {
            throw new IllegalStateException("Failed to serialize backup codes", e);
        }
    }

    public boolean verifyBackupCode(String code) {
        if (backupCodesJson == null || backupCodesJson.isBlank()) return false;

        try {
            var mapper = new com.fasterxml.jackson.databind.ObjectMapper();
            List<String> codes = mapper.readValue(backupCodesJson, List.class);
            List<String> used = usedBackupCodesJson == null || usedBackupCodesJson.isBlank()
                    ? List.of()
                    : mapper.readValue(usedBackupCodesJson, List.class);

            if (codes.contains(code) && !used.contains(code)) {
                var usedList = new java.util.ArrayList<>(used);
                used.add(code);
                this.usedBackupCodesJson = mapper.writeValueAsString(usedList);
                return true;
            }
        } catch (Exception e) {
            // ignore
        }
        return false;
    }

    public void markUsed() {
        this.signCount++;
        this.lastUsedAt = LocalDateTime.now();
    }

    public void incrementFailedAttempts(int maxAttempts, int lockoutMinutes) {
        this.failedAttempts++;
        if (this.failedAttempts >= maxAttempts) {
            this.status = MfaStatus.LOCKED;
            this.lockedUntil = LocalDateTime.now().plusMinutes(lockoutMinutes);
        }
    }

    public void resetFailedAttempts() {
        this.failedAttempts = 0;
        this.lockedUntil = null;
        if (this.status == MfaStatus.LOCKED) {
            this.status = MfaStatus.ACTIVE;
        }
    }
}
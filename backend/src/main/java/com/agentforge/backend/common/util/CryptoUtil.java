package com.agentforge.backend.common.util;

import lombok.extern.slf4j.Slf4j;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Optional;

@Slf4j
public class CryptoUtil {

    private static final String ALGORITHM = "AES/GCM/NoPadding";
    private static final int GCM_TAG_LENGTH = 128;
    private static final int IV_LENGTH = 12;
    private static final int KEY_LENGTH = 32;

    private static final Logger LOG = LoggerFactory.getLogger(CryptoUtil.class);
    private static final CryptoUtil INSTANCE = new CryptoUtil();
    private SecretKeySpec keySpec;

    private CryptoUtil() {}

    public static CryptoUtil getInstance() {
        return INSTANCE;
    }

    public void initialize(String encryptionKey) {
        if (encryptionKey == null || encryptionKey.isBlank()) {
            throw new IllegalStateException("Encryption key not configured");
        }
        
        byte[] keyBytes = Base64.getDecoder().decode(encryptionKey);
        if (keyBytes.length != KEY_LENGTH) {
            throw new IllegalArgumentException("Encryption key must be 32 bytes (256 bits) after Base64 decoding");
        }
        
        this.keySpec = new SecretKeySpec(keyBytes, "AES");
    }

    public EncryptionResult encrypt(String plaintext) {
        if (keySpec == null) {
            throw new IllegalStateException("CryptoUtil not initialized");
        }

        try {
            byte[] iv = new byte[IV_LENGTH];
            new SecureRandom().nextBytes(iv);

            Cipher cipher = Cipher.getInstance(ALGORITHM);
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.ENCRYPT_MODE, keySpec, spec);

            byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));

            // Prepend IV to ciphertext
            byte[] combined = new byte[iv.length + ciphertext.length];
            System.arraycopy(iv, 0, combined, 0, iv.length);
            System.arraycopy(ciphertext, 0, combined, iv.length, ciphertext.length);

            String encrypted = Base64.getEncoder().encodeToString(combined);
            String ivB64 = Base64.getEncoder().encodeToString(iv);

            return new EncryptionResult(encrypted, ivB64);
        } catch (Exception e) {
            LOG.error("Encryption failed", e);
            throw new IllegalStateException("Encryption failed", e);
        }
    }

    public Optional<String> decrypt(String encrypted, String ivB64) {
        if (keySpec == null) {
            throw new IllegalStateException("CryptoUtil not initialized");
        }

        try {
            byte[] combined = Base64.getDecoder().decode(encrypted);
            byte[] iv = Base64.getDecoder().decode(ivB64);

            if (combined.length < IV_LENGTH) {
                return Optional.empty();
            }

            byte[] ciphertext = new byte[combined.length - IV_LENGTH];
            System.arraycopy(combined, IV_LENGTH, ciphertext, 0, ciphertext.length);

            Cipher cipher = Cipher.getInstance(ALGORITHM);
            GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
            cipher.init(Cipher.DECRYPT_MODE, keySpec, spec);

            byte[] plaintext = cipher.doFinal(ciphertext);
            return Optional.of(new String(plaintext, StandardCharsets.UTF_8));
        } catch (Exception e) {
            LOG.debug("Decryption failed", e);
            return Optional.empty();
        }
    }

    public record EncryptionResult(String encrypted, String iv) {}
}
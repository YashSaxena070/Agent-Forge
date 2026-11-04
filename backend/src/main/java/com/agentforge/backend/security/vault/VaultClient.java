package com.agentforge.backend.security.vault;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.vault.authentication.TokenAuthentication;
import org.springframework.vault.client.VaultEndpoint;
import org.springframework.vault.core.VaultTemplate;
import reactor.core.publisher.Mono;

import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

@Component
@Slf4j
public class VaultClient {

    @org.springframework.beans.factory.annotation.Value("${vault.url:http://localhost:8200}")
    private String vaultUrl;

    @org.springframework.beans.factory.annotation.Value("${vault.token:}")
    private String token;

    @org.springframework.beans.factory.annotation.Value("${vault.namespace:}")
    private String namespace;

    @org.springframework.beans.factory.annotation.Value("${vault.mount-point:secret}")
    private String mountPoint;

    private VaultTemplate vaultTemplate;
    private final Map<String, CacheEntry> cache = new ConcurrentHashMap<>();

    @PostConstruct
    public void init() {
        VaultEndpoint endpoint = VaultEndpoint.from(vaultUrl);
        TokenAuthentication authentication = new TokenAuthentication(token);
        
        // Namespace handled by Vault configuration if provided

        this.vaultTemplate = new VaultTemplate(endpoint, authentication);
        log.info("Vault client initialized for {}", vaultUrl);
    }

    public String getSecret(String path, String key) {
        String cacheKey = path + ":" + key;
        CacheEntry cached = cache.get(cacheKey);
        if (cached != null && !cached.isExpired()) {
            return cached.value;
        }

        try {
            String fullPath = mountPoint + "/data/" + path;
            var response = vaultTemplate.read(fullPath, Map.class);
            @SuppressWarnings("unchecked")
            Map<String, Object> secret = response != null ? (Map<String, Object>) response.getData() : null;
            
            if (secret != null && secret.containsKey("data")) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) secret.get("data");
                if (data.containsKey(key)) {
                    String value = (String) data.get(key);
                    cache.put(cacheKey, new CacheEntry(value, Duration.ofMinutes(5)));
                    return value;
                }
            }
            
            log.warn("Secret not found at path: {} key: {}", path, key);
            return null;
        } catch (Exception e) {
            log.error("Failed to read secret from Vault: {}", e.getMessage());
            return null;
        }
    }

    public Map<String, String> getSecretMap(String path) {
        try {
            String fullPath = mountPoint + "/data/" + path;
            var response = vaultTemplate.read(fullPath, Map.class);
            @SuppressWarnings("unchecked")
            Map<String, Object> secret = response != null ? (Map<String, Object>) response.getData() : null;
            
            if (secret != null && secret.containsKey("data")) {
                @SuppressWarnings("unchecked")
                Map<String, Object> data = (Map<String, Object>) secret.get("data");
                return data.entrySet().stream()
                        .collect(java.util.stream.Collectors.toMap(
                                Map.Entry::getKey,
                                e -> String.valueOf(e.getValue())
                        ));
            }
            
            return Map.of();
        } catch (Exception e) {
            log.error("Failed to read secret map from Vault: {}", e.getMessage());
            return Map.of();
        }
    }

    public void writeSecret(String path, Map<String, String> data) {
        String fullPath = mountPoint + "/data/" + path;
        vaultTemplate.write(fullPath, Map.of("data", data));
        log.info("Secret written to Vault: {}", path);
        
        // Invalidate cache
        data.forEach((k, v) -> cache.remove(path + ":" + k));
    }

    public void deleteSecret(String path) {
        String fullPath = mountPoint + "/metadata/" + path;
        vaultTemplate.delete(fullPath);
        log.info("Secret deleted from Vault: {}", path);
        
        // Invalidate cache
        cache.entrySet().removeIf(entry -> entry.getKey().startsWith(path + ":"));
    }

    public String getDatabaseUrl() {
        String url = getSecret("database", "url");
        if (url == null) {
            throw new IllegalStateException("Database URL not found in Vault");
        }
        return url;
    }

    public String getJwtSecret() {
        String secret = getSecret("jwt", "secret");
        if (secret == null) {
            throw new IllegalStateException("JWT secret not found in Vault");
        }
        return secret;
    }

    public String getEncryptionKey() {
        String key = getSecret("encryption", "key");
        if (key == null) {
            throw new IllegalStateException("Encryption key not found in Vault");
        }
        return key;
    }

    public String getLlmApiKey(String provider) {
        return getSecret("llm/" + provider, "api_key");
    }

    public void rotateSecret(String path, String key, String newValue) {
        Map<String, String> current = getSecretMap(path);
        current.put(key, newValue);
        writeSecret(path, current);
        log.info("Secret rotated: {}:{}", path, key);
    }

    public boolean isHealthy() {
        try {
            vaultTemplate.read("sys/health", Map.class);
            return true;
        } catch (Exception e) {
            log.error("Vault health check failed: {}", e.getMessage());
            return false;
        }
    }

    private static class CacheEntry {
        final String value;
        final long expiresAt;

        CacheEntry(String value, Duration ttl) {
            this.value = value;
            this.expiresAt = System.currentTimeMillis() + ttl.toMillis();
        }

        boolean isExpired() {
            return System.currentTimeMillis() > expiresAt;
        }
    }
}
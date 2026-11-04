package com.agentforge.backend.security.opa;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import jakarta.annotation.PostConstruct;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@Component
@RequiredArgsConstructor
@Slf4j
public class OpaClient {

    private final ObjectMapper objectMapper = new ObjectMapper();
    private WebClient webClient;
    private String opaUrl;
    private String opaToken;

    public void initialize(String opaUrl, String opaToken) {
        this.opaUrl = opaUrl;
        this.opaToken = opaToken;

        this.webClient = WebClient.builder()
                .baseUrl(opaUrl)
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.AUTHORIZATION, "Bearer " + opaToken)
                .build();
    }

    @PostConstruct
    public void init() {
        // Will be initialized via setter injection
    }

    public void setOpaUrl(String opaUrl) {
        this.opaUrl = opaUrl;
    }

    public void setOpaToken(String opaToken) {
        this.opaToken = opaToken;
    }

    public void setWebClient(WebClient webClient) {
        this.webClient = webClient;
    }

    public PolicyDecision evaluate(PolicyInput input) {
        if (webClient == null) {
            log.warn("OPA client not initialized, allowing by default");
            return PolicyDecision.allow();
        }

        try {
            Map<String, Object> request = Map.of("input", input);
            
            JsonNode response = webClient.post()
                    .uri("/v1/data/agentforge/authz/allow")
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .timeout(Duration.ofSeconds(5))
                    .onErrorResume(e -> {
                        log.error("OPA evaluation failed: {}", e.getMessage());
                        return Mono.just(objectMapper.createObjectNode().put("result", true));
                    })
                    .block();

            if (response != null && response.has("result")) {
                boolean allowed = response.get("result").asBoolean();
                String reason = response.has("reason") ? response.get("reason").asText() : "";
                return new PolicyDecision(allowed, reason);
            }
            
            return PolicyDecision.allow();
        } catch (Exception e) {
            log.error("OPA evaluation error: {}", e.getMessage());
            return PolicyDecision.allow(); // Fail open for availability
        }
    }

    public PolicyDecision evaluate(String policyPath, Map<String, Object> input) {
        if (webClient == null) {
            return PolicyDecision.allow();
        }

        try {
            Map<String, Object> request = Map.of("input", input);
            
            JsonNode response = webClient.post()
                    .uri("/v1/data/" + policyPath)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(JsonNode.class)
                    .timeout(Duration.ofSeconds(5))
                    .onErrorResume(e -> {
                        log.error("OPA evaluation failed: {}", e.getMessage());
                        return Mono.just(objectMapper.createObjectNode().put("result", true));
                    })
                    .block();

            if (response != null && response.has("result")) {
                boolean allowed = response.get("result").asBoolean();
                String reason = response.has("reason") ? response.get("reason").asText() : "";
                return new PolicyDecision(allowed, reason);
            }
            
            return PolicyDecision.allow();
        } catch (Exception e) {
            log.error("OPA evaluation error: {}", e.getMessage());
            return PolicyDecision.allow();
        }
    }

    public boolean isHealthy() {
        if (webClient == null) return false;
        try {
            return webClient.get()
                    .uri("/health")
                    .retrieve()
                    .bodyToMono(String.class)
                    .timeout(Duration.ofSeconds(2))
                    .map(s -> true)
                    .onErrorResume(e -> Mono.just(false))
                    .blockOptional()
                    .orElse(false);
        } catch (Exception e) {
            return false;
        }
    }

    public record PolicyInput(
            Subject subject,
            String action,
            Resource resource,
            Context context
    ) {}

    public record Subject(
            String userId,
            String email,
            java.util.List<String> roles,
            java.util.List<String> permissions,
            String organizationId,
            String workspaceId
    ) {}

    public record Resource(
            String type,
            String id,
            String name,
            String ownerId,
            String organizationId,
            String workspaceId,
            String visibility,
            String dataClassification,
            Map<String, Object> metadata
    ) {}

    public record Context(
            String requestId,
            String sessionId,
            String correlationId,
            String ipAddress,
            String userAgent,
            Map<String, Object> additional
    ) {}

    public record PolicyDecision(
            boolean allowed,
            String reason,
            Map<String, Object> obligations
    ) {
        public PolicyDecision(boolean allowed, String reason) {
            this(allowed, reason, Map.of());
        }

        public static PolicyDecision allow() {
            return new PolicyDecision(true, "", Map.of());
        }

        public static PolicyDecision deny(String reason) {
            return new PolicyDecision(false, reason, Map.of());
        }
    }
}
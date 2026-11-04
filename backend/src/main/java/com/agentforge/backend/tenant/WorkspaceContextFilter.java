package com.agentforge.backend.tenant;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;
import java.util.UUID;

@Component
@RequiredArgsConstructor
@Slf4j
public class WorkspaceContextFilter extends OncePerRequestFilter {

    private final WorkspaceService workspaceService;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        String workspaceHeader = request.getHeader("X-Workspace-ID");
        String workspaceSlug = request.getHeader("X-Workspace-Slug");

        try {
            if (workspaceHeader != null && !workspaceHeader.isBlank()) {
                UUID workspaceId = UUID.fromString(workspaceHeader);
                Optional<Workspace> workspace = workspaceService.findById(workspaceId);
                workspace.ifPresent(WorkspaceContextHolder::setWorkspace);
            } else if (workspaceSlug != null && !workspaceSlug.isBlank()) {
                Optional<Workspace> workspace = workspaceService.findBySlug(workspaceSlug);
                workspace.ifPresent(WorkspaceContextHolder::setWorkspace);
            } else {
                // Try to extract from JWT claims
                String authHeader = request.getHeader("Authorization");
                if (authHeader != null && authHeader.startsWith("Bearer ")) {
                    String token = authHeader.substring(7);
                    // Extract workspace from JWT claims
                    // This would be parsed from the JWT
                }
            }
        } catch (Exception e) {
            log.warn("Failed to resolve workspace context: {}", e.getMessage());
        }

        try {
            filterChain.doFilter(request, response);
        } finally {
            WorkspaceContextHolder.clear();
        }
    }
}

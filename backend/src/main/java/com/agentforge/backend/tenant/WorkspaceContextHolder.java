package com.agentforge.backend.tenant;

import lombok.Getter;

import java.util.Optional;
import java.util.UUID;

public class WorkspaceContextHolder {

    private static final ThreadLocal<WorkspaceContext> context = new ThreadLocal<>();

    public static void setWorkspace(Workspace workspace) {
        context.set(new WorkspaceContext(workspace));
    }

    public static Optional<WorkspaceContext> getContext() {
        return Optional.ofNullable(context.get());
    }

    public static void clear() {
        context.remove();
    }

    @Getter
    public static class WorkspaceContext {
        private final Workspace workspace;

        public WorkspaceContext(Workspace workspace) {
            this.workspace = workspace;
        }

        public UUID getWorkspaceId() {
            return workspace.getId();
        }

        public String getWorkspaceSlug() {
            return workspace.getSlug();
        }

        public UUID getOrganizationId() {
            return workspace.getOrganization().getId();
        }

        public boolean isMember(UUID userId) {
            return workspace.getMembers().stream()
                    .anyMatch(m -> m.getUser().getId().equals(userId) && m.getStatus().equals("active"));
        }

        public boolean hasRole(UUID userId, String role) {
            return workspace.getMembers().stream()
                    .filter(m -> m.getUser().getId().equals(userId) && m.getStatus().equals("active"))
                    .anyMatch(m -> m.getRole().name().equalsIgnoreCase(role));
        }
    }
}
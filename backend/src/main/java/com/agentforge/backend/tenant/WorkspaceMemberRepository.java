package com.agentforge.backend.tenant;

import com.agentforge.backend.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface WorkspaceMemberRepository extends JpaRepository<WorkspaceMember, UUID> {

    Optional<WorkspaceMember> findByWorkspaceAndUser(UUID workspaceId, UUID userId);

    List<WorkspaceMember> findByWorkspaceIdAndStatus(UUID workspaceId, String status);

    @Query("SELECT m FROM WorkspaceMember m WHERE m.workspace.id = :workspaceId AND m.user.id = :userId")
    Optional<WorkspaceMember> findByWorkspaceAndUserNative(
            @Param("workspaceId") UUID workspaceId,
            @Param("userId") UUID userId);

    boolean existsByWorkspaceAndUser(UUID workspaceId, UUID userId);

    @Query("SELECT m FROM WorkspaceMember m WHERE m.workspace.id = :workspaceId AND m.role IN :roles AND m.status = 'active'")
    List<WorkspaceMember> findByWorkspaceAndRoles(
            @Param("workspaceId") UUID workspaceId,
            @Param("roles") List<String> roles);
}
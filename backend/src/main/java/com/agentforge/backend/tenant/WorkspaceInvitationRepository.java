package com.agentforge.backend.tenant;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface WorkspaceInvitationRepository extends JpaRepository<WorkspaceInvitation, UUID> {

    Optional<WorkspaceInvitation> findByToken(String token);

    List<WorkspaceInvitation> findByWorkspaceIdAndStatus(UUID workspaceId, String status);

    @Query("SELECT i FROM WorkspaceInvitation i WHERE i.workspace.id = :workspaceId AND i.email = :email")
    Optional<WorkspaceInvitation> findByWorkspaceAndEmail(
            @Param("workspaceId") UUID workspaceId,
            @Param("email") String email);
}
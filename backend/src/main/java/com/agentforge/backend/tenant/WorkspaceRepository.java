package com.agentforge.backend.tenant;

import com.agentforge.backend.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface WorkspaceRepository extends JpaRepository<Workspace, UUID> {

    Optional<Workspace> findBySlug(String slug);

    Optional<Workspace> findBySlugAndOrganizationId(String slug, UUID organizationId);

    List<Workspace> findByOrganizationId(UUID organizationId);

    @Query("SELECT w FROM Workspace w JOIN w.members m WHERE m.user.id = :userId AND m.status = 'active' AND w.status = 'active'")
    List<Workspace> findActiveWorkspacesByUser(@Param("userId") UUID userId);

    boolean existsBySlugAndOrganizationId(String slug, UUID organizationId);
}
package com.agentforge.backend.project.repository;

import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.project.Project;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ProjectRepository
        extends JpaRepository<Project, UUID> {

    List<Project> findAllByOrganization(
            Organization organization
    );

    List<Project> findAllByOrganizationAndStatusNot(
            Organization organization,
            ProjectStatus status
    );

    Optional<Project>
    findByIdAndOrganization(
            UUID id,
            Organization organization
    );

    boolean existsByOrganizationAndSlug(
            Organization organization,
            String slug
    );

    Optional<Project>
    findByOrganizationAndSlug(
            Organization organization,
            String slug
    );
}
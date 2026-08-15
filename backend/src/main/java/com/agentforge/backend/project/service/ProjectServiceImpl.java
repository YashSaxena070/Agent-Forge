package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.service.OrganizationAccessService;
import com.agentforge.backend.project.dto.CreateProjectRequest;
import com.agentforge.backend.project.dto.ProjectResponse;
import com.agentforge.backend.project.dto.UpdateProjectRequest;
import com.agentforge.backend.project.exception.ProjectNotFoundException;
import com.agentforge.backend.project.exception.ProjectSlugAlreadyExistsException;
import com.agentforge.backend.project.repository.ProjectMemberRepository;
import com.agentforge.backend.project.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ProjectServiceImpl
        implements ProjectService {

    private final ProjectRepository projectRepository;

    private final OrganizationAccessService organizationAccessService;
    private final ProjectMemberRepository projectMemberRepository;

    @Override
    @Transactional
    public ProjectResponse createProject(
            UUID organizationId,
            CreateProjectRequest request,
            User user
    ) {

        /*
         * OWNER, ADMIN and DEVELOPER can
         * create projects.
         */
        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN,
                OrganizationRole.DEVELOPER
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        String slug =
                generateUniqueSlug(
                        organization,
                        request.name()
                );

        Project project =
                Project.builder()
                        .organization(organization)
                        .name(request.name())
                        .slug(slug)
                        .description(
                                request.description()
                        )
                        .status(ProjectStatus.DRAFT)
                        .build();

        Project saved =
                projectRepository.save(project);

        ProjectMember projectMember =
                ProjectMember.builder()
                        .project(saved)
                        .user(user)
                        .role(ProjectRole.PROJECT_ADMIN)
                        .build();

        projectMemberRepository.save(
                projectMember
        );

        return toResponse(saved);
    }

    @Override
    @Transactional(readOnly = true)
    public List<ProjectResponse> getProjects(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        return projectRepository
                .findAllByOrganizationAndStatusNot(
                        organization,
                        ProjectStatus.DELETED
                )
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public ProjectResponse getProject(
            UUID organizationId,
            UUID projectId,
            User user
    ) {

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        Project project =
                findProject(
                        projectId,
                        organization
                );

        return toResponse(project);
    }

    @Override
    @Transactional
    public ProjectResponse updateProject(
            UUID organizationId,
            UUID projectId,
            UpdateProjectRequest request,
            User user
    ) {

        /*
         * Only OWNER and ADMIN can modify
         * project metadata for now.
         */
        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        Project project =
                findProject(
                        projectId,
                        organization
                );

        project.setName(
                request.name()
        );

        project.setDescription(
                request.description()
        );

        return toResponse(
                projectRepository.save(project)
        );
    }

    @Override
    @Transactional
    public void archiveProject(
            UUID organizationId,
            UUID projectId,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        Project project =
                findProject(
                        projectId,
                        organization
                );

        project.setStatus(
                ProjectStatus.ARCHIVED
        );

        projectRepository.save(project);
    }

    @Override
    @Transactional
    public void deleteProject(
            UUID organizationId,
            UUID projectId,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        Project project =
                findProject(
                        projectId,
                        organization
                );

        /*
         * Soft delete.
         */
        project.setStatus(
                ProjectStatus.DELETED
        );

        projectRepository.save(project);
    }

    private Project findProject(
            UUID projectId,
            Organization organization
    ) {

        return projectRepository
                .findByIdAndOrganization(
                        projectId,
                        organization
                )
                .filter(project ->
                        project.getStatus()
                                != ProjectStatus.DELETED
                )
                .orElseThrow(() ->
                        new ProjectNotFoundException(
                                "Project not found."
                        )
                );
    }

    private String generateUniqueSlug(
            Organization organization,
            String name
    ) {

        String baseSlug =
                name
                        .toLowerCase()
                        .trim()
                        .replaceAll(
                                "[^a-z0-9]+",
                                "-"
                        )
                        .replaceAll(
                                "^-|-$",
                                ""
                        );

        if (baseSlug.isBlank()) {
            baseSlug = "project";
        }

        String slug = baseSlug;

        int counter = 1;

        while (
                projectRepository
                        .existsByOrganizationAndSlug(
                                organization,
                                slug
                        )
        ) {

            slug =
                    baseSlug
                            + "-"
                            + counter++;
        }

        return slug;
    }

    private ProjectResponse toResponse(
            Project project
    ) {

        return ProjectResponse.builder()
                .id(project.getId())
                .organizationId(
                        project
                                .getOrganization()
                                .getId()
                )
                .name(project.getName())
                .slug(project.getSlug())
                .description(
                        project.getDescription()
                )
                .status(project.getStatus())
                .createdAt(project.getCreatedAt())
                .updatedAt(project.getUpdatedAt())
                .build();
    }
}
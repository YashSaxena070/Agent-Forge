package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.project.exception.ProjectAccessDeniedException;
import com.agentforge.backend.project.exception.ProjectNotFoundException;
import com.agentforge.backend.project.repository.ProjectMemberRepository;
import com.agentforge.backend.project.repository.ProjectRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ProjectAccessServiceImpl
        implements ProjectAccessService {

    private final ProjectRepository projectRepository;

    private final ProjectMemberRepository
            projectMemberRepository;

    private final OrganizationMemberRepository
            organizationMemberRepository;

    @Override
    public ProjectMember getMembership(
            UUID projectId,
            User user
    ) {

        Project project =
                getProjectById(projectId);

        /*
         * Organization OWNER/ADMIN automatically
         * have elevated project access.
         *
         * We still return the actual ProjectMember
         * when one exists.
         */
        return projectMemberRepository
                .findByProjectAndUser(
                        project,
                        user
                )
                .orElseThrow(() ->
                        new ProjectAccessDeniedException(
                                "You are not a member of this project."
                        )
                );
    }

    @Override
    public Project getProject(
            UUID projectId,
            User user
    ) {

        Project project =
                getProjectById(projectId);

        requireOrganizationAccess(
                project,
                user
        );

        return project;
    }

    @Override
    public void requireMember(
            UUID projectId,
            User user
    ) {

        Project project =
                getProjectById(projectId);

        /*
         * Organization OWNER and ADMIN can access
         * all projects inside their organization.
         */
        if (hasOrganizationManagementAccess(
                project,
                user
        )) {
            return;
        }

        projectMemberRepository
                .findByProjectAndUser(
                        project,
                        user
                )
                .orElseThrow(() ->
                        new ProjectAccessDeniedException(
                                "You are not a member of this project."
                        )
                );
    }

    @Override
    public void requireRole(
            UUID projectId,
            User user,
            ProjectRole... allowedRoles
    ) {

        Project project =
                getProjectById(projectId);

        /*
         * Organization OWNER has complete
         * project access.
         */
        if (hasOrganizationOwnerAccess(
                project,
                user
        )) {
            return;
        }

        /*
         * Organization ADMIN can manage projects.
         */
        if (hasOrganizationAdminAccess(
                project,
                user
        )) {

            boolean projectAdminAllowed =
                    Arrays.asList(allowedRoles)
                            .contains(
                                    ProjectRole.PROJECT_ADMIN
                            );

            if (projectAdminAllowed) {
                return;
            }
        }

        ProjectMember membership =
                projectMemberRepository
                        .findByProjectAndUser(
                                project,
                                user
                        )
                        .orElseThrow(() ->
                                new ProjectAccessDeniedException(
                                        "You are not a member of this project."
                                )
                        );

        if (!Arrays.asList(allowedRoles)
                .contains(membership.getRole())) {

            throw new ProjectAccessDeniedException(
                    "You do not have permission to perform this action."
            );
        }
    }

    @Override
    public boolean hasRole(
            UUID projectId,
            User user,
            ProjectRole... roles
    ) {

        Project project =
                getProjectById(projectId);

        if (hasOrganizationOwnerAccess(
                project,
                user
        )) {
            return true;
        }

        if (hasOrganizationAdminAccess(
                project,
                user
        )) {

            return Arrays.asList(roles)
                    .contains(
                            ProjectRole.PROJECT_ADMIN
                    );
        }

        return projectMemberRepository
                .findByProjectAndUser(
                        project,
                        user
                )
                .map(member ->
                        Arrays.asList(roles)
                                .contains(
                                        member.getRole()
                                )
                )
                .orElse(false);
    }

    private void requireOrganizationAccess(
            Project project,
            User user
    ) {

        if (hasOrganizationManagementAccess(
                project,
                user
        )) {
            return;
        }

        boolean projectMember =
                projectMemberRepository
                        .existsByProjectAndUser(
                                project,
                                user
                        );

        if (!projectMember) {

            throw new ProjectAccessDeniedException(
                    "You do not have access to this project."
            );
        }
    }

    private boolean hasOrganizationManagementAccess(
            Project project,
            User user
    ) {

        return hasOrganizationOwnerAccess(
                project,
                user
        )
                ||
                hasOrganizationAdminAccess(
                        project,
                        user
                );
    }

    private boolean hasOrganizationOwnerAccess(
            Project project,
            User user
    ) {

        return getOrganizationRole(
                project,
                user
        ) == OrganizationRole.OWNER;
    }

    private boolean hasOrganizationAdminAccess(
            Project project,
            User user
    ) {

        OrganizationRole role =
                getOrganizationRole(
                        project,
                        user
                );

        return role == OrganizationRole.ADMIN;
    }

    private OrganizationRole getOrganizationRole(
            Project project,
            User user
    ) {

        return organizationMemberRepository
                .findByOrganizationAndUser(
                        project.getOrganization(),
                        user
                )
                .map(OrganizationMember::getRole)
                .orElse(null);
    }

    private Project getProjectById(
            UUID projectId
    ) {

        return projectRepository
                .findById(projectId)
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
}
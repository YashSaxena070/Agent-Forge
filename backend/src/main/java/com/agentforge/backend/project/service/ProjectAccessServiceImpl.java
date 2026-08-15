package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;
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

    @Override
    public ProjectMember getMembership(
            UUID projectId,
            User user
    ) {

        Project project =
                getProjectById(projectId);

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

        getMembership(
                projectId,
                user
        );

        return getProjectById(projectId);
    }

    @Override
    public void requireMember(
            UUID projectId,
            User user
    ) {

        getMembership(
                projectId,
                user
        );
    }

    @Override
    public void requireRole(
            UUID projectId,
            User user,
            ProjectRole... allowedRoles
    ) {

        ProjectMember membership =
                getMembership(
                        projectId,
                        user
                );

        ProjectRole currentRole =
                membership.getRole();

        boolean allowed =
                Arrays.asList(allowedRoles)
                        .contains(currentRole);

        if (!allowed) {

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

        ProjectMember membership =
                getMembership(
                        projectId,
                        user
                );

        return Arrays.asList(roles)
                .contains(
                        membership.getRole()
                );
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
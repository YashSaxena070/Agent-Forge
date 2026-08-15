package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.user.UserRepository;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.project.dto.*;
import com.agentforge.backend.project.exception.ProjectAccessDeniedException;
import com.agentforge.backend.project.repository.ProjectMemberRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class ProjectMemberServiceImpl
        implements ProjectMemberService {

    private final ProjectMemberRepository
            projectMemberRepository;

    private final OrganizationMemberRepository
            organizationMemberRepository;

    private final UserRepository userRepository;

    private final ProjectAccessService
            projectAccessService;

    @Override
    @Transactional(readOnly = true)
    public List<ProjectMemberResponse> getMembers(
            UUID projectId,
            User user
    ) {

        Project project =
                projectAccessService.getProject(
                        projectId,
                        user
                );

        return projectMemberRepository
                .findAllByProject(project)
                .stream()
                .map(this::toResponse)
                .toList();
    }

    @Override
    @Transactional
    public ProjectMemberResponse addMember(
            UUID projectId,
            AddProjectMemberRequest request,
            User user
    ) {

        projectAccessService.requireRole(
                projectId,
                user,
                ProjectRole.PROJECT_ADMIN
        );

        Project project =
                projectAccessService.getProject(
                        projectId,
                        user
                );

        User targetUser =
                userRepository
                        .findById(request.userId())
                        .orElseThrow(() ->
                                new ProjectAccessDeniedException(
                                        "User not found."
                                )
                        );

        /*
         * User must belong to the same organization.
         */
        OrganizationMember organizationMember =
                organizationMemberRepository
                        .findByOrganizationAndUser(
                                project.getOrganization(),
                                targetUser
                        )
                        .orElseThrow(() ->
                                new ProjectAccessDeniedException(
                                        "User is not a member of this organization."
                                )
                        );

        /*
         * Prevent duplicate project membership.
         */
        if (projectMemberRepository
                .existsByProjectAndUser(
                        project,
                        targetUser
                )) {

            throw new ProjectAccessDeniedException(
                    "User is already a member of this project."
            );
        }

        ProjectMember member =
                ProjectMember.builder()
                        .project(project)
                        .user(targetUser)
                        .role(request.role())
                        .build();

        return toResponse(
                projectMemberRepository.save(member)
        );
    }

    @Override
    @Transactional
    public void changeRole(
            UUID projectId,
            UUID memberId,
            ChangeProjectMemberRoleRequest request,
            User user
    ) {

        projectAccessService.requireRole(
                projectId,
                user,
                ProjectRole.PROJECT_ADMIN
        );

        Project project =
                projectAccessService.getProject(
                        projectId,
                        user
                );

        ProjectMember member =
                projectMemberRepository
                        .findByIdAndProject(
                                memberId,
                                project
                        )
                        .orElseThrow(() ->
                                new ProjectAccessDeniedException(
                                        "Project member not found."
                                )
                        );

        member.setRole(
                request.role()
        );

        projectMemberRepository.save(member);
    }

    @Override
    @Transactional
    public void removeMember(
            UUID projectId,
            UUID memberId,
            User user
    ) {

        projectAccessService.requireRole(
                projectId,
                user,
                ProjectRole.PROJECT_ADMIN
        );

        Project project =
                projectAccessService.getProject(
                        projectId,
                        user
                );

        ProjectMember member =
                projectMemberRepository
                        .findByIdAndProject(
                                memberId,
                                project
                        )
                        .orElseThrow(() ->
                                new ProjectAccessDeniedException(
                                        "Project member not found."
                                )
                        );

        /*
         * Don't allow admin to remove themselves
         * through this endpoint.
         */
        if (member.getUser()
                .getId()
                .equals(user.getId())) {

            throw new ProjectAccessDeniedException(
                    "Use leave project instead."
            );
        }

        projectMemberRepository.delete(member);
    }

    @Override
    @Transactional
    public void leaveProject(
            UUID projectId,
            User user
    ) {

        Project project =
                projectAccessService.getProject(
                        projectId,
                        user
                );

        ProjectMember member =
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

        /*
         * Don't allow the last PROJECT_ADMIN
         * to leave.
         */
        if (member.getRole()
                == ProjectRole.PROJECT_ADMIN) {

            long adminCount =
                    projectMemberRepository
                            .findAllByProject(project)
                            .stream()
                            .filter(projectMember ->
                                    projectMember.getRole()
                                            == ProjectRole.PROJECT_ADMIN
                            )
                            .count();

            if (adminCount <= 1) {

                throw new ProjectAccessDeniedException(
                        "The last project administrator cannot leave the project."
                );
            }
        }

        projectMemberRepository.delete(member);
    }

    private ProjectMemberResponse toResponse(
            ProjectMember member
    ) {

        User memberUser =
                member.getUser();

        return ProjectMemberResponse.builder()
                .id(member.getId())
                .userId(memberUser.getId())
                .fullName(memberUser.getFullName())
                .email(memberUser.getEmail())
                .role(member.getRole())
                .joinedAt(member.getCreatedAt())
                .build();
    }
}
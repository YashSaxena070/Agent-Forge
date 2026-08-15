package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;

import java.util.UUID;

public interface ProjectAccessService {

    ProjectMember getMembership(
            UUID projectId,
            User user
    );

    Project getProject(
            UUID projectId,
            User user
    );

    void requireMember(
            UUID projectId,
            User user
    );

    void requireRole(
            UUID projectId,
            User user,
            ProjectRole... allowedRoles
    );

    boolean hasRole(
            UUID projectId,
            User user,
            ProjectRole... roles
    );
}
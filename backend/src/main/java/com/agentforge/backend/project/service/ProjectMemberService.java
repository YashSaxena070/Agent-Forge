package com.agentforge.backend.project.service;

import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.project.dto.*;

import java.util.List;
import java.util.UUID;

public interface ProjectMemberService {

    List<ProjectMemberResponse> getMembers(
            UUID projectId,
            User user
    );

    ProjectMemberResponse addMember(
            UUID projectId,
            AddProjectMemberRequest request,
            User user
    );

    void changeRole(
            UUID projectId,
            UUID memberId,
            ChangeProjectMemberRoleRequest request,
            User user
    );

    void removeMember(
            UUID projectId,
            UUID memberId,
            User user
    );

    void leaveProject(
            UUID projectId,
            User user
    );
}
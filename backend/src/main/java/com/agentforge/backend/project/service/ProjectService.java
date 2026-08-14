package com.agentforge.backend.project.service;

import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.project.dto.CreateProjectRequest;
import com.agentforge.backend.project.dto.ProjectResponse;
import com.agentforge.backend.project.dto.UpdateProjectRequest;

import java.util.List;
import java.util.UUID;

public interface ProjectService {

    ProjectResponse createProject(
            UUID organizationId,
            CreateProjectRequest request,
            User user
    );

    List<ProjectResponse> getProjects(
            UUID organizationId,
            User user
    );

    ProjectResponse getProject(
            UUID organizationId,
            UUID projectId,
            User user
    );

    ProjectResponse updateProject(
            UUID organizationId,
            UUID projectId,
            UpdateProjectRequest request,
            User user
    );

    void archiveProject(
            UUID organizationId,
            UUID projectId,
            User user
    );

    void deleteProject(
            UUID organizationId,
            UUID projectId,
            User user
    );
}
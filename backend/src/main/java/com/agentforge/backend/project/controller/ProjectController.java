package com.agentforge.backend.project.controller;

import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.project.dto.CreateProjectRequest;
import com.agentforge.backend.project.dto.ProjectResponse;
import com.agentforge.backend.project.dto.UpdateProjectRequest;
import com.agentforge.backend.project.service.ProjectService;
import com.agentforge.backend.security.auth.CustomUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping(
        "/api/v1/organizations/{organizationId}/projects"
)
@RequiredArgsConstructor
public class ProjectController {

    private final ProjectService projectService;

    @PostMapping
    public ResponseEntity<
            ApiResponse<ProjectResponse>
            > createProject(

            @PathVariable
            UUID organizationId,

            @Valid
            @RequestBody
            CreateProjectRequest request,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        ProjectResponse response =
                projectService.createProject(
                        organizationId,
                        request,
                        user
                );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        ApiResponse
                                .<ProjectResponse>builder()
                                .success(true)
                                .message(
                                        "Project created successfully."
                                )
                                .data(response)
                                .timestamp(
                                        LocalDateTime.now()
                                )
                                .build()
                );
    }

    @GetMapping
    public ResponseEntity<
            ApiResponse<List<ProjectResponse>>
            > getProjects(

            @PathVariable
            UUID organizationId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        List<ProjectResponse> projects =
                projectService.getProjects(
                        organizationId,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<List<ProjectResponse>>builder()
                        .success(true)
                        .message(
                                "Projects retrieved successfully."
                        )
                        .data(projects)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @GetMapping("/{projectId}")
    public ResponseEntity<
            ApiResponse<ProjectResponse>
            > getProject(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID projectId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        ProjectResponse project =
                projectService.getProject(
                        organizationId,
                        projectId,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<ProjectResponse>builder()
                        .success(true)
                        .message(
                                "Project retrieved successfully."
                        )
                        .data(project)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @PutMapping("/{projectId}")
    public ResponseEntity<
            ApiResponse<ProjectResponse>
            > updateProject(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID projectId,

            @Valid
            @RequestBody
            UpdateProjectRequest request,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        ProjectResponse project =
                projectService.updateProject(
                        organizationId,
                        projectId,
                        request,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<ProjectResponse>builder()
                        .success(true)
                        .message(
                                "Project updated successfully."
                        )
                        .data(project)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @PostMapping("/{projectId}/archive")
    public ResponseEntity<ApiResponse<Void>>
    archiveProject(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID projectId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        projectService.archiveProject(
                organizationId,
                projectId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Project archived successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @DeleteMapping("/{projectId}")
    public ResponseEntity<ApiResponse<Void>>
    deleteProject(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID projectId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        projectService.deleteProject(
                organizationId,
                projectId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Project deleted successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    private User getUser(
            Authentication authentication
    ) {

        CustomUserDetails userDetails =
                (CustomUserDetails)
                        authentication.getPrincipal();

        return userDetails.getUser();
    }
}
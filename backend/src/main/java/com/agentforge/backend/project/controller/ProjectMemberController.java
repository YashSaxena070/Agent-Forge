package com.agentforge.backend.project.controller;

import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.project.dto.*;
import com.agentforge.backend.project.service.ProjectMemberService;
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
        "/api/v1/projects/{projectId}/members"
)
@RequiredArgsConstructor
public class ProjectMemberController {

    private final ProjectMemberService
            projectMemberService;

    @GetMapping
    public ResponseEntity<
            ApiResponse<List<ProjectMemberResponse>>
            > getMembers(

            @PathVariable
            UUID projectId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        List<ProjectMemberResponse> members =
                projectMemberService.getMembers(
                        projectId,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<List<ProjectMemberResponse>>builder()
                        .success(true)
                        .message(
                                "Project members retrieved successfully."
                        )
                        .data(members)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @PostMapping
    public ResponseEntity<
            ApiResponse<ProjectMemberResponse>
            > addMember(

            @PathVariable
            UUID projectId,

            @Valid
            @RequestBody
            AddProjectMemberRequest request,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        ProjectMemberResponse member =
                projectMemberService.addMember(
                        projectId,
                        request,
                        user
                );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        ApiResponse
                                .<ProjectMemberResponse>builder()
                                .success(true)
                                .message(
                                        "Project member added successfully."
                                )
                                .data(member)
                                .timestamp(
                                        LocalDateTime.now()
                                )
                                .build()
                );
    }

    @PatchMapping("/{memberId}/role")
    public ResponseEntity<ApiResponse<Void>>
    changeRole(

            @PathVariable
            UUID projectId,

            @PathVariable
            UUID memberId,

            @Valid
            @RequestBody
            ChangeProjectMemberRoleRequest request,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        projectMemberService.changeRole(
                projectId,
                memberId,
                request,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Project member role updated successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @DeleteMapping("/{memberId}")
    public ResponseEntity<ApiResponse<Void>>
    removeMember(

            @PathVariable
            UUID projectId,

            @PathVariable
            UUID memberId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        projectMemberService.removeMember(
                projectId,
                memberId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Project member removed successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @DeleteMapping("/me")
    public ResponseEntity<ApiResponse<Void>>
    leaveProject(

            @PathVariable
            UUID projectId,

            Authentication authentication

    ) {

        User user =
                getUser(authentication);

        projectMemberService.leaveProject(
                projectId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "You left the project successfully."
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
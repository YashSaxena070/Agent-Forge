package com.agentforge.backend.organization.controller;

import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.*;
import com.agentforge.backend.organization.service.OrganizationService;
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
@RequestMapping("/api/v1/organizations")
@RequiredArgsConstructor
public class OrganizationController {

    private final OrganizationService organizationService;

    @PostMapping
    public ResponseEntity<
            ApiResponse<OrganizationResponse>
            > createOrganization(

            @Valid
            @RequestBody
            CreateOrganizationRequest request,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        OrganizationResponse response =
                organizationService.createOrganization(
                        request,
                        user
                );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        ApiResponse
                                .<OrganizationResponse>builder()
                                .success(true)
                                .message(
                                        "Organization created successfully."
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
            ApiResponse<List<OrganizationResponse>>
            > getMyOrganizations(

            Authentication authentication

    ) {

        User user = getUser(authentication);

        List<OrganizationResponse> organizations =
                organizationService
                        .getMyOrganizations(user);

        return ResponseEntity.ok(
                ApiResponse
                        .<List<OrganizationResponse>>builder()
                        .success(true)
                        .message(
                                "Organizations retrieved successfully."
                        )
                        .data(organizations)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @GetMapping("/{organizationId}")
    public ResponseEntity<
            ApiResponse<OrganizationResponse>
            > getOrganization(

            @PathVariable
            UUID organizationId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        OrganizationResponse response =
                organizationService.getOrganization(
                        organizationId,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<OrganizationResponse>builder()
                        .success(true)
                        .message(
                                "Organization retrieved successfully."
                        )
                        .data(response)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @PutMapping("/{organizationId}")
    public ResponseEntity<
            ApiResponse<OrganizationResponse>
            > updateOrganization(

            @PathVariable
            UUID organizationId,

            @Valid
            @RequestBody
            UpdateOrganizationRequest request,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        OrganizationResponse response =
                organizationService.updateOrganization(
                        organizationId,
                        request,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<OrganizationResponse>builder()
                        .success(true)
                        .message(
                                "Organization updated successfully."
                        )
                        .data(response)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @DeleteMapping("/{organizationId}")
    public ResponseEntity<ApiResponse<Void>> deleteOrganization(

            @PathVariable
            UUID organizationId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        organizationService.deleteOrganization(
                organizationId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Organization deleted successfully."
                        )
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @GetMapping("/{organizationId}/members")
    public ResponseEntity<
            ApiResponse<List<MemberResponse>>
            > getMembers(

            @PathVariable
            UUID organizationId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        List<MemberResponse> members =
                organizationService.getMembers(
                        organizationId,
                        user
                );

        return ResponseEntity.ok(
                ApiResponse
                        .<List<MemberResponse>>builder()
                        .success(true)
                        .message(
                                "Organization members retrieved successfully."
                        )
                        .data(members)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @PatchMapping(
            "/{organizationId}/members/{memberId}/role"
    )
    public ResponseEntity<ApiResponse<Void>>
    changeMemberRole(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID memberId,

            @Valid
            @RequestBody
            ChangeMemberRoleRequest request,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        organizationService.changeMemberRole(
                organizationId,
                memberId,
                request,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Member role updated successfully."
                        )
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @DeleteMapping(
            "/{organizationId}/members/{memberId}"
    )
    public ResponseEntity<ApiResponse<Void>>
    removeMember(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID memberId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        organizationService.removeMember(
                organizationId,
                memberId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Member removed successfully."
                        )
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @PostMapping(
            "/{organizationId}/transfer-ownership"
    )
    public ResponseEntity<ApiResponse<Void>>
    transferOwnership(

            @PathVariable
            UUID organizationId,

            @Valid
            @RequestBody
            TransferOwnershipRequest request,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        organizationService.transferOwnership(
                organizationId,
                request,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Organization ownership transferred successfully."
                        )
                        .data(null)
                        .timestamp(LocalDateTime.now())
                        .build()
        );
    }

    @DeleteMapping("/{organizationId}/members/me")
    public ResponseEntity<ApiResponse<Void>>
    leaveOrganization(

            @PathVariable
            UUID organizationId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        organizationService.leaveOrganization(
                organizationId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "You left the organization successfully."
                        )
                        .data(null)
                        .timestamp(LocalDateTime.now())
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
package com.agentforge.backend.organization.controller;

import com.agentforge.backend.common.response.ApiResponse;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.InvitationResponse;
import com.agentforge.backend.organization.dto.InviteMemberRequest;
import com.agentforge.backend.organization.service.OrganizationInvitationService;
import com.agentforge.backend.security.auth.CustomUserDetails;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/organizations")
@RequiredArgsConstructor
public class OrganizationInvitationController {

    private final OrganizationInvitationService
            invitationService;

    @PostMapping("/{organizationId}/members/invite")
    public ResponseEntity<
            ApiResponse<InvitationResponse>
            > inviteMember(

            @PathVariable
            UUID organizationId,

            @Valid
            @RequestBody
            InviteMemberRequest request,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        InvitationResponse response =
                invitationService.inviteMember(
                        organizationId,
                        request,
                        user
                );

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(
                        ApiResponse
                                .<InvitationResponse>builder()
                                .success(true)
                                .message(
                                        "Invitation created successfully."
                                )
                                .data(response)
                                .timestamp(
                                        LocalDateTime.now()
                                )
                                .build()
                );
    }

    @PostMapping(
            "/invitations/{token}/accept"
    )
    public ResponseEntity<
            ApiResponse<Void>
            > acceptInvitation(

            @PathVariable
            String token,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        invitationService.acceptInvitation(
                token,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Invitation accepted successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @PostMapping(
            "/invitations/{token}/reject"
    )
    public ResponseEntity<
            ApiResponse<Void>
            > rejectInvitation(

            @PathVariable
            String token,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        invitationService.rejectInvitation(
                token,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Invitation rejected successfully."
                        )
                        .data(null)
                        .timestamp(
                                LocalDateTime.now()
                        )
                        .build()
        );
    }

    @DeleteMapping(
            "/{organizationId}/invitations/{invitationId}"
    )
    public ResponseEntity<
            ApiResponse<Void>
            > cancelInvitation(

            @PathVariable
            UUID organizationId,

            @PathVariable
            UUID invitationId,

            Authentication authentication

    ) {

        User user = getUser(authentication);

        invitationService.cancelInvitation(
                organizationId,
                invitationId,
                user
        );

        return ResponseEntity.ok(
                ApiResponse.<Void>builder()
                        .success(true)
                        .message(
                                "Invitation cancelled successfully."
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
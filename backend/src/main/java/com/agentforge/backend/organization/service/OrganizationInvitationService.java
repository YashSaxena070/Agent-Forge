package com.agentforge.backend.organization.service;

import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.InvitationResponse;
import com.agentforge.backend.organization.dto.InviteMemberRequest;

import java.util.UUID;

public interface OrganizationInvitationService {

    InvitationResponse inviteMember(
            UUID organizationId,
            InviteMemberRequest request,
            User invitedBy
    );

    void acceptInvitation(
            String token,
            User user
    );

    void rejectInvitation(
            String token,
            User user
    );

    void cancelInvitation(
            UUID organizationId,
            UUID invitationId,
            User user
    );
}
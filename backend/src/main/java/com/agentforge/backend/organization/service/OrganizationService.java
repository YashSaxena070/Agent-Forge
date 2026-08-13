package com.agentforge.backend.organization.service;

import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.*;

import java.util.List;
import java.util.UUID;

public interface OrganizationService {

    OrganizationResponse createOrganization(
            CreateOrganizationRequest request,
            User user
    );

    List<OrganizationResponse> getMyOrganizations(
            User user
    );

    OrganizationResponse getOrganization(
            UUID organizationId,
            User user
    );

    OrganizationResponse updateOrganization(
            UUID organizationId,
            UpdateOrganizationRequest request,
            User user
    );

    void deleteOrganization(
            UUID organizationId,
            User user
    );

    List<MemberResponse> getMembers(
            UUID organizationId,
            User user
    );

    void changeMemberRole(
            UUID organizationId,
            UUID memberId,
            ChangeMemberRoleRequest request,
            User user
    );

    void removeMember(
            UUID organizationId,
            UUID memberId,
            User user
    );

    void transferOwnership(
            UUID organizationId,
            TransferOwnershipRequest request,
            User user
    );

    void leaveOrganization(
            UUID organizationId,
            User user
    );
}
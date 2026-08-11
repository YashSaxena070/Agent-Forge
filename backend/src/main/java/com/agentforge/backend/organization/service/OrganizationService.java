package com.agentforge.backend.organization.service;

import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.CreateOrganizationRequest;
import com.agentforge.backend.organization.dto.OrganizationResponse;
import com.agentforge.backend.organization.dto.UpdateOrganizationRequest;

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
}
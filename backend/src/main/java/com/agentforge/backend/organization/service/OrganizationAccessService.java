package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;

import java.util.UUID;

public interface OrganizationAccessService {

    OrganizationMember getMembership(
            UUID organizationId,
            User user
    );

    Organization getOrganization(
            UUID organizationId,
            User user
    );

    void requireMember(
            UUID organizationId,
            User user
    );

    void requireRole(
            UUID organizationId,
            User user,
            OrganizationRole... allowedRoles
    );

    boolean hasRole(
            UUID organizationId,
            User user,
            OrganizationRole... roles
    );
}
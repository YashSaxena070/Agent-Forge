package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.exception.OrganizationAccessDeniedException;
import com.agentforge.backend.organization.exception.OrganizationNotFoundException;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.organization.repository.OrganizationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class OrganizationAccessServiceImpl
        implements OrganizationAccessService {

    private final OrganizationRepository organizationRepository;

    private final OrganizationMemberRepository
            organizationMemberRepository;

    @Override
    public OrganizationMember getMembership(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                getOrganizationById(organizationId);

        return organizationMemberRepository
                .findByOrganizationAndUser(
                        organization,
                        user
                )
                .orElseThrow(() ->
                        new OrganizationAccessDeniedException(
                                "You are not a member of this organization."
                        )
                );
    }

    @Override
    public Organization getOrganization(
            UUID organizationId,
            User user
    ) {

        getMembership(
                organizationId,
                user
        );

        return getOrganizationById(organizationId);
    }

    @Override
    public void requireMember(
            UUID organizationId,
            User user
    ) {

        getMembership(
                organizationId,
                user
        );
    }

    @Override
    public void requireRole(
            UUID organizationId,
            User user,
            OrganizationRole... allowedRoles
    ) {

        OrganizationMember membership =
                getMembership(
                        organizationId,
                        user
                );

        OrganizationRole currentRole =
                membership.getRole();

        boolean allowed =
                Arrays.asList(allowedRoles)
                        .contains(currentRole);

        if (!allowed) {

            throw new OrganizationAccessDeniedException(
                    "You do not have permission to perform this action."
            );
        }
    }

    @Override
    public boolean hasRole(
            UUID organizationId,
            User user,
            OrganizationRole... roles
    ) {

        OrganizationMember membership =
                getMembership(
                        organizationId,
                        user
                );

        return Arrays.asList(roles)
                .contains(membership.getRole());
    }

    private Organization getOrganizationById(
            UUID organizationId
    ) {

        return organizationRepository
                .findById(organizationId)
                .orElseThrow(() ->
                        new OrganizationNotFoundException(
                                "Organization not found."
                        )
                );
    }
}
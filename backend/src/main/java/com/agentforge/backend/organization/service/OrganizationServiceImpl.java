package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.CreateOrganizationRequest;
import com.agentforge.backend.organization.dto.OrganizationResponse;
import com.agentforge.backend.organization.dto.UpdateOrganizationRequest;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.organization.repository.OrganizationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.agentforge.backend.organization.exception.OrganizationNotFoundException;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class OrganizationServiceImpl
        implements OrganizationService {

    private final OrganizationRepository organizationRepository;

    private final OrganizationMemberRepository organizationMemberRepository;
    private final OrganizationAccessService organizationAccessService;

    @Override
    @Transactional
    public OrganizationResponse createOrganization(
            CreateOrganizationRequest request,
            User user
    ) {

        String slug = generateUniqueSlug(request.name());

        Organization organization =
                Organization.builder()
                        .name(request.name())
                        .slug(slug)
                        .description(request.description())
                        .logoUrl(request.logoUrl())
                        .build();

        Organization savedOrganization =
                organizationRepository.save(organization);

        OrganizationMember owner =
                OrganizationMember.builder()
                        .organization(savedOrganization)
                        .user(user)
                        .role(OrganizationRole.OWNER)
                        .build();

        organizationMemberRepository.save(owner);

        return toResponse(savedOrganization);
    }

    @Override
    @Transactional(readOnly = true)
    public List<OrganizationResponse> getMyOrganizations(User user) {

        return organizationMemberRepository
                .findAllByUser(user)
                .stream()
                .map(member ->
                        toResponse(
                                member.getOrganization()
                        )
                )
                .toList();
    }

    @Override
    @Transactional(readOnly = true)
    public OrganizationResponse getOrganization(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                getOrganizationIfMember(
                        organizationId,
                        user
                );

        return toResponse(organization);
    }

    @Override
    public OrganizationResponse updateOrganization(UUID organizationId, UpdateOrganizationRequest request, User user) {
        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationRepository
                        .findById(organizationId)
                        .orElseThrow(() ->
                                new OrganizationNotFoundException(
                                        "Organization not found."
                                )
                        );

        organization.setName(request.name());

        organization.setDescription(
                request.description()
        );

        organization.setLogoUrl(
                request.logoUrl()
        );

        Organization updated =
                organizationRepository.save(organization);

        return toResponse(updated);
    }

    @Override
    @Transactional
    public void deleteOrganization(
            UUID organizationId,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER
        );

        Organization organization =
                organizationRepository
                        .findById(organizationId)
                        .orElseThrow(() ->
                                new OrganizationNotFoundException(
                                        "Organization not found."
                                )
                        );

        organizationRepository.delete(organization);
    }

    private Organization getOrganizationIfMember(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                organizationRepository
                        .findById(organizationId)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Organization not found."
                                )
                        );

        boolean member =
                organizationMemberRepository
                        .existsByOrganizationAndUser(
                                organization,
                                user
                        );

        if (!member) {
            throw new RuntimeException(
                    "You are not a member of this organization."
            );
        }

        return organization;
    }


    private String generateUniqueSlug(
            String name
    ) {

        String baseSlug =
                name
                        .toLowerCase()
                        .trim()
                        .replaceAll(
                                "[^a-z0-9]+",
                                "-"
                        )
                        .replaceAll(
                                "^-|-$",
                                ""
                        );

        String slug = baseSlug;

        int counter = 1;

        while (
                organizationRepository
                        .existsBySlug(slug)
        ) {

            slug =
                    baseSlug
                            + "-"
                            + counter++;
        }

        return slug;
    }

    private OrganizationResponse toResponse(
            Organization organization
    ) {

        return OrganizationResponse.builder()
                .id(organization.getId())
                .name(organization.getName())
                .slug(organization.getSlug())
                .description(organization.getDescription())
                .logoUrl(organization.getLogoUrl())
                .createdAt(organization.getCreatedAt())
                .updatedAt(organization.getUpdatedAt())
                .build();
    }
}
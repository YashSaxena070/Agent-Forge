package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.*;
import com.agentforge.backend.organization.exception.OrganizationAccessDeniedException;
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

    @Override
    @Transactional(readOnly = true)
    public List<MemberResponse> getMembers(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        return organizationMemberRepository
                .findAllByOrganization(organization)
                .stream()
                .map(this::toMemberResponse)
                .toList();
    }

    @Override
    @Transactional
    public void changeMemberRole(
            UUID organizationId,
            UUID memberId,
            ChangeMemberRoleRequest request,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        OrganizationMember targetMember =
                organizationMemberRepository
                        .findByIdAndOrganization(
                                memberId,
                                organization
                        )
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Organization member not found."
                                )
                        );

        /*
         * OWNER cannot be changed through this API.
         */
        if (targetMember.getRole()
                == OrganizationRole.OWNER) {

            throw new OrganizationAccessDeniedException(
                    "Owner role cannot be changed here."
            );
        }

        /*
         * OWNER cannot be assigned through
         * normal role management.
         */
        if (request.role()
                == OrganizationRole.OWNER) {

            throw new OrganizationAccessDeniedException(
                    "Use ownership transfer to assign OWNER role."
            );
        }

        /*
         * ADMIN must not be able to promote
         * another member to ADMIN.
         *
         * Only OWNER can manage ADMIN roles.
         */
        if (request.role()
                == OrganizationRole.ADMIN) {

            organizationAccessService.requireRole(
                    organizationId,
                    user,
                    OrganizationRole.OWNER
            );
        }

        targetMember.setRole(
                request.role()
        );

        organizationMemberRepository.save(
                targetMember
        );
    }

    @Override
    @Transactional
    public void removeMember(
            UUID organizationId,
            UUID memberId,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        OrganizationMember targetMember =
                organizationMemberRepository
                        .findByIdAndOrganization(
                                memberId,
                                organization
                        )
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "Organization member not found."
                                )
                        );

        /*
         * Owner cannot be removed.
         */
        if (targetMember.getRole()
                == OrganizationRole.OWNER) {

            throw new OrganizationAccessDeniedException(
                    "The organization owner cannot be removed."
            );
        }

        /*
         * ADMIN cannot remove another ADMIN.
         */
        if (targetMember.getRole()
                == OrganizationRole.ADMIN) {

            organizationAccessService.requireRole(
                    organizationId,
                    user,
                    OrganizationRole.OWNER
            );
        }

        organizationMemberRepository.delete(
                targetMember
        );
    }

    @Override
    @Transactional
    public void transferOwnership(
            UUID organizationId,
            TransferOwnershipRequest request,
            User user
    ) {

        /*
         * Only current owner can transfer ownership.
         */
        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER
        );

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        OrganizationMember currentOwner =
                organizationMemberRepository
                        .findByOrganizationAndUser(
                                organization,
                                user
                        )
                        .orElseThrow(() ->
                                new OrganizationAccessDeniedException(
                                        "Current owner membership not found."
                                )
                        );

        OrganizationMember newOwner =
                organizationMemberRepository
                        .findByIdAndOrganization(
                                request.memberId(),
                                organization
                        )
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "New owner member not found."
                                )
                        );

        if (currentOwner.getId()
                .equals(newOwner.getId())) {

            throw new OrganizationAccessDeniedException(
                    "You are already the owner."
            );
        }

        /*
         * Atomic ownership transfer:
         *
         * OLD OWNER -> ADMIN
         * NEW OWNER -> OWNER
         */
        currentOwner.setRole(
                OrganizationRole.ADMIN
        );

        newOwner.setRole(
                OrganizationRole.OWNER
        );

        organizationMemberRepository.save(
                currentOwner
        );

        organizationMemberRepository.save(
                newOwner
        );
    }

    @Override
    @Transactional
    public void leaveOrganization(
            UUID organizationId,
            User user
    ) {

        Organization organization =
                organizationAccessService.getOrganization(
                        organizationId,
                        user
                );

        OrganizationMember membership =
                organizationMemberRepository
                        .findByOrganizationAndUser(
                                organization,
                                user
                        )
                        .orElseThrow(() ->
                                new OrganizationAccessDeniedException(
                                        "You are not a member of this organization."
                                )
                        );

        /*
         * Owner cannot leave.
         *
         * Ownership must first be transferred.
         */
        if (membership.getRole()
                == OrganizationRole.OWNER) {

            throw new OrganizationAccessDeniedException(
                    "Owner must transfer ownership before leaving."
            );
        }

        organizationMemberRepository.delete(
                membership
        );
    }


    private MemberResponse toMemberResponse(
            OrganizationMember member
    ) {

        User memberUser =
                member.getUser();

        return MemberResponse.builder()

                .id(member.getId())

                .userId(memberUser.getId())

                .fullName(memberUser.getFullName())

                .email(memberUser.getEmail())

                .role(member.getRole())

                .emailVerified(
                        memberUser.isEmailVerified()
                )

                .joinedAt(member.getCreatedAt())

                .build();
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
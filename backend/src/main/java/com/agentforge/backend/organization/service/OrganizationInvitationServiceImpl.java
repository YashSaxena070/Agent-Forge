package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.InvitationStatus;
import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationInvitation;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.InvitationResponse;
import com.agentforge.backend.organization.dto.InviteMemberRequest;
import com.agentforge.backend.organization.exception.InvalidInvitationException;
import com.agentforge.backend.organization.exception.InvitationNotFoundException;
import com.agentforge.backend.organization.exception.MemberAlreadyExistsException;
import com.agentforge.backend.organization.repository.OrganizationInvitationRepository;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.organization.repository.OrganizationRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class OrganizationInvitationServiceImpl
        implements OrganizationInvitationService {

    private final OrganizationRepository organizationRepository;

    private final OrganizationMemberRepository
            organizationMemberRepository;

    private final OrganizationInvitationRepository
            invitationRepository;

    private final OrganizationAccessService
            organizationAccessService;

    @Override
    @Transactional
    public InvitationResponse inviteMember(
            UUID organizationId,
            InviteMemberRequest request,
            User invitedBy
    ) {

        /*
         * OWNER and ADMIN can invite members.
         */
        organizationAccessService.requireRole(
                organizationId,
                invitedBy,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        /*
         * OWNER cannot be assigned through invitation.
         */
        if (request.role() == OrganizationRole.OWNER) {

            throw new InvalidInvitationException(
                    "Owner role cannot be assigned through an invitation."
            );
        }

        Organization organization =
                organizationRepository
                        .findById(organizationId)
                        .orElseThrow(() ->
                                new InvalidInvitationException(
                                        "Organization not found."
                                )
                        );

        String email =
                request.email()
                        .trim()
                        .toLowerCase();

        /*
         * Check if user is already a member of the organization.
         */
        boolean alreadyMember =
                organizationMemberRepository
                        .existsByOrganizationAndUser_EmailIgnoreCase(
                                organization,
                                email
                        );

        if (alreadyMember) {

            throw new MemberAlreadyExistsException(
                    "User is already a member of this organization."
            );
        }

        /*
         * We can check pending invitation duplicates.
         */
        boolean pendingInvitation =
                invitationRepository
                        .existsByOrganizationAndEmailAndStatus(
                                organization,
                                email,
                                InvitationStatus.PENDING
                        );

        if (pendingInvitation) {

            throw new InvalidInvitationException(
                    "A pending invitation already exists for this email."
            );
        }

        /*
         * Generate cryptographically secure token.
         */
        String token =
                UUID.randomUUID().toString()
                        + "-"
                        + UUID.randomUUID();

        /*
         * Invitation expires in 7 days.
         */
        LocalDateTime expiresAt =
                LocalDateTime.now()
                        .plusDays(7);

        OrganizationInvitation invitation =
                OrganizationInvitation.builder()

                        .organization(organization)

                        .invitedBy(invitedBy)

                        .email(email)

                        .token(token)

                        .role(request.role())

                        .status(
                                InvitationStatus.PENDING
                        )

                        .expiresAt(expiresAt)

                        .build();

        OrganizationInvitation saved =
                invitationRepository.save(
                        invitation
                );

        return toResponse(saved);
    }

    @Override
    @Transactional
    public void acceptInvitation(
            String token,
            User user
    ) {

        OrganizationInvitation invitation =
                invitationRepository
                        .findByToken(token)
                        .orElseThrow(() ->
                                new InvitationNotFoundException(
                                        "Invitation not found."
                                )
                        );

        /*
         * Check invitation state.
         */
        if (invitation.getStatus()
                != InvitationStatus.PENDING) {

            throw new InvalidInvitationException(
                    "This invitation is no longer active."
            );
        }

        /*
         * Check expiration.
         */
        if (invitation.getExpiresAt()
                .isBefore(LocalDateTime.now())) {

            invitation.setStatus(
                    InvitationStatus.EXPIRED
            );

            invitationRepository.save(invitation);

            throw new InvalidInvitationException(
                    "This invitation has expired."
            );
        }

        /*
         * Security:
         *
         * Only the invited email can accept.
         */
        if (!user.getEmail()
                .equalsIgnoreCase(
                        invitation.getEmail()
                )) {

            throw new InvalidInvitationException(
                    "This invitation was issued for another email address."
            );
        }

        Organization organization =
                invitation.getOrganization();

        /*
         * Prevent duplicate membership.
         */
        if (organizationMemberRepository
                .existsByOrganizationAndUser(
                        organization,
                        user
                )) {

            throw new MemberAlreadyExistsException(
                    "You are already a member of this organization."
            );
        }

        /*
         * Create organization membership.
         */
        OrganizationMember member =
                OrganizationMember.builder()

                        .organization(organization)

                        .user(user)

                        .role(invitation.getRole())

                        .build();

        organizationMemberRepository.save(member);

        /*
         * Mark invitation accepted.
         */
        invitation.setStatus(
                InvitationStatus.ACCEPTED
        );

        invitation.setAcceptedAt(
                LocalDateTime.now()
        );

        invitationRepository.save(invitation);
    }

    @Override
    @Transactional
    public void rejectInvitation(
            String token,
            User user
    ) {

        OrganizationInvitation invitation =
                invitationRepository
                        .findByToken(token)
                        .orElseThrow(() ->
                                new InvitationNotFoundException(
                                        "Invitation not found."
                                )
                        );

        if (!invitation.getEmail()
                .equalsIgnoreCase(
                        user.getEmail()
                )) {

            throw new InvalidInvitationException(
                    "You cannot reject this invitation."
            );
        }

        if (invitation.getStatus()
                != InvitationStatus.PENDING) {

            throw new InvalidInvitationException(
                    "This invitation is no longer active."
            );
        }

        invitation.setStatus(
                InvitationStatus.REJECTED
        );

        invitationRepository.save(invitation);
    }

    @Override
    @Transactional
    public void cancelInvitation(
            UUID organizationId,
            UUID invitationId,
            User user
    ) {

        organizationAccessService.requireRole(
                organizationId,
                user,
                OrganizationRole.OWNER,
                OrganizationRole.ADMIN
        );

        OrganizationInvitation invitation =
                invitationRepository
                        .findById(invitationId)
                        .orElseThrow(() ->
                                new InvitationNotFoundException(
                                        "Invitation not found."
                                )
                        );

        if (!invitation
                .getOrganization()
                .getId()
                .equals(organizationId)) {

            throw new InvalidInvitationException(
                    "Invitation does not belong to this organization."
            );
        }

        if (invitation.getStatus()
                != InvitationStatus.PENDING) {

            throw new InvalidInvitationException(
                    "Only pending invitations can be cancelled."
            );
        }

        invitation.setStatus(
                InvitationStatus.CANCELLED
        );

        invitationRepository.save(invitation);
    }

    private InvitationResponse toResponse(
            OrganizationInvitation invitation
    ) {

        return InvitationResponse.builder()

                .id(invitation.getId())

                .organizationId(
                        invitation
                                .getOrganization()
                                .getId()
                )

                .organizationName(
                        invitation
                                .getOrganization()
                                .getName()
                )

                .email(invitation.getEmail())

                .role(invitation.getRole())

                .status(invitation.getStatus())

                .expiresAt(
                        invitation.getExpiresAt()
                )

                /*
                 * Development only.
                 */
                .invitationToken(
                        invitation.getToken()
                )

                .build();
    }
}
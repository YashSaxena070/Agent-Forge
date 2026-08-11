package com.agentforge.backend.organization.repository;

import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationInvitation;
import com.agentforge.backend.common.enums.InvitationStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface OrganizationInvitationRepository
        extends JpaRepository<
        OrganizationInvitation,
        UUID
        > {

    Optional<OrganizationInvitation>
    findByToken(String token);

    List<OrganizationInvitation>
    findAllByOrganization(
            Organization organization
    );

    List<OrganizationInvitation>
    findAllByOrganizationAndStatus(
            Organization organization,
            InvitationStatus status
    );

    boolean existsByOrganizationAndEmailAndStatus(
            Organization organization,
            String email,
            InvitationStatus status
    );
}
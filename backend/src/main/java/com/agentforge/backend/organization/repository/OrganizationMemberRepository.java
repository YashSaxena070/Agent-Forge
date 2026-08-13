package com.agentforge.backend.organization.repository;

import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface OrganizationMemberRepository
        extends JpaRepository<OrganizationMember, UUID> {

    Optional<OrganizationMember>
    findByOrganizationAndUser(
            Organization organization,
            User user
    );

    Optional<OrganizationMember> findByIdAndOrganization(
            UUID id,
            Organization organization
    );

    List<OrganizationMember> findAllByUser(User user);

    List<OrganizationMember> findAllByOrganization(Organization organization);

    boolean existsByOrganizationAndUser(
            Organization organization,
            User user
    );

    long countByOrganization(
            Organization organization
    );
}
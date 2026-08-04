package com.agentforge.backend.domain.repository;

import com.agentforge.backend.domain.entity.OrganizationMember;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface OrganizationMemberRepository extends JpaRepository<OrganizationMember, UUID> {
}

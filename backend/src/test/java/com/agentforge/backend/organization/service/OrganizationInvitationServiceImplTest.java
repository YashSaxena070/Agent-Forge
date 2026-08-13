package com.agentforge.backend.organization.service;

import com.agentforge.backend.common.enums.OrganizationRole;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationInvitation;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.dto.InviteMemberRequest;
import com.agentforge.backend.organization.exception.MemberAlreadyExistsException;
import com.agentforge.backend.organization.repository.OrganizationInvitationRepository;
import com.agentforge.backend.organization.repository.OrganizationMemberRepository;
import com.agentforge.backend.organization.repository.OrganizationRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;

import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrganizationInvitationServiceImplTest {

    @Mock
    private OrganizationRepository organizationRepository;

    @Mock
    private OrganizationMemberRepository organizationMemberRepository;

    @Mock
    private OrganizationInvitationRepository invitationRepository;

    @Mock
    private OrganizationAccessService organizationAccessService;

    @InjectMocks
    private OrganizationInvitationServiceImpl invitationService;

    private UUID organizationId;
    private User invitedBy;
    private Organization organization;

    @BeforeEach
    void setUp() {
        organizationId = UUID.randomUUID();
        invitedBy = User.builder().email("admin@gmail.com").build();
        organization = Organization.builder().name("Test Org").build();
    }

    @Test
    void inviteMember_whenUserIsAlreadyMember_throwsMemberAlreadyExistsException() {
        String existingEmail = "developer1@gmail.com";
        InviteMemberRequest request = new InviteMemberRequest(existingEmail, OrganizationRole.DEVELOPER);

        when(organizationRepository.findById(organizationId)).thenReturn(Optional.of(organization));
        when(organizationMemberRepository.existsByOrganizationAndUser_EmailIgnoreCase(organization, existingEmail))
                .thenReturn(true);

        MemberAlreadyExistsException exception = assertThrows(
                MemberAlreadyExistsException.class,
                () -> invitationService.inviteMember(organizationId, request, invitedBy)
        );

        assertEquals("User is already a member of this organization.", exception.getMessage());
        verify(invitationRepository, never()).save(any(OrganizationInvitation.class));
    }
}

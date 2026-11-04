package com.agentforge.backend.tenant;

import com.agentforge.backend.audit.AuditService;
import com.agentforge.backend.audit.AuditService.AuditEvent;
import com.agentforge.backend.common.enums.UserStatus;
import com.agentforge.backend.common.enums.SystemRole;
import com.agentforge.backend.common.exception.NotFoundException;
import com.agentforge.backend.common.exception.AccessDeniedException;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.organization.repository.OrganizationRepository;
import com.agentforge.backend.domain.user.UserRepository;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class WorkspaceService {

    private final WorkspaceRepository workspaceRepository;
    private final WorkspaceMemberRepository memberRepository;
    private final WorkspaceInvitationRepository invitationRepository;
    private final UserRepository userRepository;
    private final AuditService auditService;
    private final OrganizationRepository organizationRepository;

    public Optional<Workspace> findById(UUID id) {
        return workspaceRepository.findById(id);
    }

    public Optional<Workspace> findBySlug(String slug) {
        return workspaceRepository.findBySlug(slug);
    }

    public List<Workspace> findByOrganizationId(UUID organizationId) {
        return workspaceRepository.findByOrganizationId(organizationId);
    }

    public List<Workspace> findActiveWorkspacesByUser(UUID userId) {
        return workspaceRepository.findActiveWorkspacesByUser(userId);
    }

    @Transactional
    public Workspace createWorkspace(UUID organizationId, UUID userId, CreateWorkspaceRequest request) {
        // Verify user has permission in organization
        // Implementation would check organization membership

        Organization organization = organizationRepository.findById(organizationId)
                .orElseThrow(() -> new NotFoundException("Organization not found"));

        Workspace workspace = Workspace.builder()
                .organization(organization)
                .name(request.name())
                .slug(request.slug())
                .description(request.description())
                .visibility(request.visibility())
                .settings(request.settings())
                .defaultTechStack(request.defaultTechStack())
                .maxProjects(request.maxProjects())
                .maxConcurrentWorkflows(request.maxConcurrentWorkflows())
                .storageLimitGb(request.storageLimitGb())
                .build();

        Workspace saved = workspaceRepository.save(workspace);

        // Add creator as owner
        User user = userRepository.findById(userId).orElseThrow();
        WorkspaceMember owner = WorkspaceMember.builder()
                .workspace(saved)
                .user(user)
                .role(MemberRole.OWNER)
                .status("active")
                .joinedAt(LocalDateTime.now())
                .build();
        memberRepository.save(owner);

        auditService.log(new AuditEvent(
                "workspace.created", "INFO", userId, "user",
                "workspace", saved.getId(), saved.getName(),
                "create", "SUCCESS", Map.of("organization_id", organizationId.toString()),
                0, List.of(), List.of("workspace_management"), "internal"
        ));

        return saved;
    }

    @Transactional
    public WorkspaceInvitation inviteMember(UUID workspaceId, UUID inviterId, InviteMemberRequest request) {
        Workspace workspace = workspaceRepository.findById(workspaceId)
                .orElseThrow(() -> new NotFoundException("Workspace not found"));

        // Check inviter has permission
        WorkspaceMember inviter = memberRepository.findByWorkspaceAndUser(workspaceId, inviterId)
                .orElseThrow(() -> new AccessDeniedException("Not a member of this workspace"));
        
        if (!inviter.getRole().canInvite()) {
            throw new AccessDeniedException("Insufficient permissions to invite members");
        }

        // Check if user already exists
        User user = userRepository.findByEmail(request.email())
                .orElse(null);

        if (user != null && memberRepository.existsByWorkspaceAndUser(workspaceId, user.getId())) {
            throw new IllegalStateException("User is already a member");
        }

        String token = UUID.randomUUID().toString();
        WorkspaceInvitation invitation = WorkspaceInvitation.builder()
                .workspace(workspace)
                .email(request.email())
                .role(request.role())
                .token(token)
                .expiresAt(LocalDateTime.now().plusDays(7))
                .invitedByUser(userRepository.findById(inviterId).orElseThrow())
                .build();

        WorkspaceInvitation saved = invitationRepository.save(invitation);

        // Send invitation email (async)
        // emailService.sendInvitation(saved);

        auditService.log(new AuditEvent(
                "workspace.member.invited", "INFO", inviterId, "user",
                "workspace_invitation", saved.getId(), null,
                "invite", "SUCCESS", Map.of("email", request.email(), "role", request.role().name()),
                0, List.of(), List.of("workspace_management"), "internal"
        ));

        return saved;
    }

    @Transactional
    public void acceptInvitation(String token, UUID userId) {
        WorkspaceInvitation invitation = invitationRepository.findByToken(token)
                .orElseThrow(() -> new NotFoundException("Invitation not found"));

        if (!invitation.isPending()) {
            throw new IllegalStateException("Invitation is no longer valid");
        }

        User user = userRepository.findById(userId).orElseThrow();
        
        if (!user.getEmail().equalsIgnoreCase(invitation.getEmail())) {
            throw new AccessDeniedException("Invitation email does not match user email");
        }

        Workspace workspace = invitation.getWorkspace();
        
        // Check if already member
        if (memberRepository.existsByWorkspaceAndUser(workspace.getId(), userId)) {
            invitation.setStatus("accepted");
            invitation.setAcceptedAt(LocalDateTime.now());
            invitation.setAcceptedBy(userId);
            invitationRepository.save(invitation);
            return;
        }

        WorkspaceMember member = WorkspaceMember.builder()
                .workspace(workspace)
                .user(user)
                .role(invitation.getRole())
                .status("active")
                .joinedAt(LocalDateTime.now())
                .invitedBy(invitation.getInvitedByUser().getId())
                .build();
        memberRepository.save(member);

        invitation.setStatus("accepted");
        invitation.setAcceptedAt(LocalDateTime.now());
        invitation.setAcceptedBy(userId);
        invitationRepository.save(invitation);

        auditService.log(new AuditEvent(
                "workspace.member.joined", "INFO", userId, "user",
                "workspace_member", member.getId(), null,
                "accept_invitation", "SUCCESS", Map.of("workspace_id", workspace.getId().toString()),
                0, List.of(), List.of("workspace_management"), "internal"
        ));
    }

    @Transactional
    public void removeMember(UUID workspaceId, UUID requesterId, UUID targetUserId) {
        Workspace workspace = workspaceRepository.findById(workspaceId)
                .orElseThrow(() -> new NotFoundException("Workspace not found"));

        WorkspaceMember requester = memberRepository.findByWorkspaceAndUser(workspaceId, requesterId)
                .orElseThrow(() -> new AccessDeniedException("Not a member of this workspace"));

        if (!requester.getRole().canRemoveMembers()) {
            throw new AccessDeniedException("Insufficient permissions to remove members");
        }

        if (requesterId.equals(targetUserId)) {
            throw new IllegalStateException("Cannot remove yourself");
        }

        memberRepository.findByWorkspaceAndUser(workspaceId, targetUserId)
                .ifPresent(member -> {
                    member.setStatus("removed");
                    memberRepository.save(member);
                });

        auditService.log(new AuditEvent(
                "workspace.member.removed", "WARNING", requesterId, "user",
                "workspace_member", targetUserId, null,
                "remove_member", "SUCCESS", Map.of("workspace_id", workspaceId.toString()),
                20, List.of(), List.of("workspace_management", "security"), "internal"
        ));
    }

    public List<WorkspaceMember> getMembers(UUID workspaceId) {
        return memberRepository.findByWorkspaceIdAndStatus(workspaceId, "active");
    }

    public record CreateWorkspaceRequest(
            String name,
            String slug,
            String description,
            String visibility,
            Map<String, String> settings,
            List<String> defaultTechStack,
            int maxProjects,
            int maxConcurrentWorkflows,
            int storageLimitGb
    ) {}

    public record InviteMemberRequest(
            String email,
            MemberRole role
    ) {}
}
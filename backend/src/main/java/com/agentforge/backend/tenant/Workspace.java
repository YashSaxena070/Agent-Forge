package com.agentforge.backend.tenant;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.organization.OrganizationMember;
import com.agentforge.backend.domain.project.Project;
import jakarta.persistence.*;
import lombok.*;

import java.util.*;

@Entity
@Table(name = "workspaces",
        uniqueConstraints = {
                @UniqueConstraint(columnNames = {"organization_id", "slug"})
        })
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Workspace extends BaseEntity {

    @Id
    @GeneratedValue
    @Column(name = "id", columnDefinition = "uuid", updatable = false, nullable = false)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "organization_id", nullable = false)
    private Organization organization;

    @Column(name = "name", nullable = false, length = 255)
    private String name;

    @Column(name = "slug", nullable = false, length = 100)
    private String slug;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "visibility", length = 50)
    private String visibility = "private";

    @ElementCollection
    @CollectionTable(name = "workspace_settings", joinColumns = @JoinColumn(name = "workspace_id"))
    @MapKeyColumn(name = "setting_key")
    @Column(name = "setting_value")
    @Builder.Default
    private Map<String, String> settings = new HashMap<>();

    @ElementCollection
    @CollectionTable(name = "workspace_default_tech_stack", joinColumns = @JoinColumn(name = "workspace_id"))
    @Column(name = "technology")
    @Builder.Default
    private List<String> defaultTechStack = new ArrayList<>();

    @Column(name = "max_projects")
    private int maxProjects = 50;

    @Column(name = "max_concurrent_workflows")
    private int maxConcurrentWorkflows = 10;

    @Column(name = "storage_limit_gb")
    private int storageLimitGb = 5;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20)
    private WorkspaceStatus status = WorkspaceStatus.ACTIVE;

    @OneToMany(mappedBy = "workspace", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<WorkspaceMember> members = new ArrayList<>();

    @OneToMany(mappedBy = "workspace", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<Project> projects = new ArrayList<>();

    @OneToMany(mappedBy = "workspace", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<WorkspaceInvitation> invitations = new ArrayList<>();

    public boolean isMember(UUID userId) {
        return members.stream()
                .anyMatch(m -> m.getUser().getId().equals(userId) && m.getStatus().equals("active"));
    }

    public boolean hasRole(UUID userId, String role) {
        return members.stream()
                .filter(m -> m.getUser().getId().equals(userId) && m.getStatus().equals("active"))
                .anyMatch(m -> m.getRole().name().equalsIgnoreCase(role));
    }

    public Optional<WorkspaceMember> getMember(UUID userId) {
        return members.stream()
                .filter(m -> m.getUser().getId().equals(userId) && m.getStatus().equals("active"))
                .findFirst();
    }
}
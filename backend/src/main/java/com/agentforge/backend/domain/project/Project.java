package com.agentforge.backend.domain.project;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.organization.Organization;
import jakarta.persistence.*;
import lombok.*;


@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(
        name = "projects",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_project_org_slug",
                        columnNames = {
                                "organization_id",
                                "slug"
                        }
                )
        },
        indexes = {
                @Index(
                        name = "idx_project_organization",
                        columnList = "organization_id"
                )
        }
)
public class Project extends BaseEntity {

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "organization_id",
            nullable = false
    )
    private Organization organization;

    @Column(
            nullable = false,
            length = 100
    )
    private String name;

    @Column(
            nullable = false,
            length = 120
    )
    private String slug;

    @Column(length = 1000)
    private String description;

    @Enumerated(EnumType.STRING)
    @Column(
            nullable = false,
            length = 30
    )
    @Builder.Default
    private ProjectStatus status =
            ProjectStatus.DRAFT;
}
package com.agentforge.backend.domain.project;

import com.agentforge.backend.common.entity.BaseEntity;
import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.domain.user.User;
import jakarta.persistence.*;
import lombok.*;

@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(
        name = "project_members",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_project_member_user",
                        columnNames = {
                                "project_id",
                                "user_id"
                        }
                )
        },
        indexes = {
                @Index(
                        name = "idx_project_member_project",
                        columnList = "project_id"
                ),
                @Index(
                        name = "idx_project_member_user",
                        columnList = "user_id"
                )
        }
)
public class ProjectMember extends BaseEntity {

    @ManyToOne(
            fetch = FetchType.LAZY,
            optional = false
    )
    @JoinColumn(
            name = "project_id",
            nullable = false
    )
    private Project project;

    @ManyToOne(
            fetch = FetchType.LAZY,
            optional = false
    )
    @JoinColumn(
            name = "user_id",
            nullable = false
    )
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(
            nullable = false,
            length = 30
    )
    @Builder.Default
    private ProjectRole role =
            ProjectRole.DEVELOPER;
}
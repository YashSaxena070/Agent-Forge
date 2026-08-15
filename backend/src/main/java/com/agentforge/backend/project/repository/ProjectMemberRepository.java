package com.agentforge.backend.project.repository;

import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.project.ProjectMember;
import com.agentforge.backend.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ProjectMemberRepository
        extends JpaRepository<ProjectMember, UUID> {

    Optional<ProjectMember>
    findByProjectAndUser(
            Project project,
            User user
    );

    Optional<ProjectMember>
    findByIdAndProject(
            UUID memberId,
            Project project
    );

    List<ProjectMember>
    findAllByProject(
            Project project
    );

    boolean existsByProjectAndUser(
            Project project,
            User user
    );

    void deleteByProjectAndUser(
            Project project,
            User user
    );
}
package com.agentforge.backend.project.service;

import com.agentforge.backend.common.enums.ProjectRole;
import com.agentforge.backend.common.enums.ProjectStatus;
import com.agentforge.backend.domain.organization.Organization;
import com.agentforge.backend.domain.project.Project;
import com.agentforge.backend.domain.user.User;
import com.agentforge.backend.organization.service.OrganizationAccessService;
import com.agentforge.backend.project.dto.CreateProjectRequest;
import com.agentforge.backend.project.dto.ProjectResponse;
import com.agentforge.backend.project.repository.ProjectMemberRepository;
import com.agentforge.backend.project.repository.ProjectRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class ProjectServiceImplTest {

    @Mock
    private ProjectRepository projectRepository;

    @Mock
    private OrganizationAccessService organizationAccessService;

    @Mock
    private ProjectMemberRepository projectMemberRepository;

    @Mock
    private ProjectAccessService projectAccessService;

    @InjectMocks
    private ProjectServiceImpl projectService;

    private UUID organizationId;
    private User user;
    private Organization organization;

    @BeforeEach
    void setUp() {
        organizationId = UUID.randomUUID();
        user = User.builder()
                .email("test@agentforge.com")
                .build();

        organization = Organization.builder()
                .name("Test Org")
                .slug("test-org")
                .build();
    }

    @Test
    void createProject_success() {
        CreateProjectRequest request = new CreateProjectRequest("Test Project", "Description");

        when(organizationAccessService.getOrganization(eq(organizationId), eq(user)))
                .thenReturn(organization);
        when(projectRepository.existsByOrganizationAndSlug(any(), anyString()))
                .thenReturn(false);

        Project savedProject = Project.builder()
                .organization(organization)
                .name(request.name())
                .slug("test-project")
                .description(request.description())
                .status(ProjectStatus.DRAFT)
                .build();

        when(projectRepository.save(any(Project.class))).thenReturn(savedProject);

        ProjectResponse response = projectService.createProject(organizationId, request, user);

        assertNotNull(response);
        assertEquals("Test Project", response.name());
        verify(projectMemberRepository, times(1)).save(any());
    }
}

CREATE TABLE projects (

    id UUID NOT NULL,

    created_at TIMESTAMP NOT NULL,

    updated_at TIMESTAMP,

    organization_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,

    slug VARCHAR(120) NOT NULL,

    description VARCHAR(1000),

    status VARCHAR(30) NOT NULL,

    CONSTRAINT pk_projects
        PRIMARY KEY (id),

    CONSTRAINT fk_projects_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    CONSTRAINT uk_project_org_slug
        UNIQUE (
            organization_id,
            slug
        ),

    CONSTRAINT chk_project_status
        CHECK (
            status IN (
                'DRAFT',
                'ACTIVE',
                'ARCHIVED',
                'DELETED'
            )
        )
);

CREATE INDEX idx_project_organization
    ON projects(organization_id);

CREATE INDEX idx_project_organization_status
    ON projects(
        organization_id,
        status
    );
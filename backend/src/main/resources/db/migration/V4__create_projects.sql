CREATE TABLE projects
(
    id UUID PRIMARY KEY,

    organization_id UUID NOT NULL,

    name VARCHAR(100) NOT NULL,

    description VARCHAR(1000),

    status VARCHAR(30) NOT NULL,

    created_at TIMESTAMP NOT NULL,

    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_project_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE
);
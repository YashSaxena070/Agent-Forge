CREATE TABLE project_members (

    id UUID NOT NULL,

    created_at TIMESTAMP NOT NULL,

    updated_at TIMESTAMP,

    project_id UUID NOT NULL,

    user_id UUID NOT NULL,

    role VARCHAR(30) NOT NULL,

    CONSTRAINT pk_project_members
        PRIMARY KEY (id),

    CONSTRAINT uk_project_member_user
        UNIQUE (
            project_id,
            user_id
        ),

    CONSTRAINT fk_project_member_project
        FOREIGN KEY (project_id)
        REFERENCES projects(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_project_member_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT chk_project_member_role
        CHECK (
            role IN (
                'PROJECT_ADMIN',
                'DEVELOPER',
                'VIEWER'
            )
        )
);

CREATE INDEX idx_project_member_project
    ON project_members(project_id);

CREATE INDEX idx_project_member_user
    ON project_members(user_id);
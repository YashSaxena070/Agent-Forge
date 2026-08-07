CREATE TABLE organization_members
(
    id UUID PRIMARY KEY,

    organization_id UUID NOT NULL,

    user_id UUID NOT NULL,

    role VARCHAR(30) NOT NULL,

    created_at TIMESTAMP NOT NULL,

    updated_at TIMESTAMP NOT NULL,

    CONSTRAINT fk_member_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_member_user
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    CONSTRAINT uk_organization_user
        UNIQUE (organization_id, user_id)
);
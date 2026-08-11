CREATE TABLE organization_invitations (

    id UUID NOT NULL,

    created_at TIMESTAMP NOT NULL,

    updated_at TIMESTAMP,

    organization_id UUID NOT NULL,

    invited_by UUID NOT NULL,

    email VARCHAR(320) NOT NULL,

    token VARCHAR(512) NOT NULL,

    role VARCHAR(30) NOT NULL,

    status VARCHAR(30) NOT NULL,

    expires_at TIMESTAMP NOT NULL,

    accepted_at TIMESTAMP,

    CONSTRAINT pk_organization_invitations
        PRIMARY KEY (id),

    CONSTRAINT uk_organization_invitations_token
        UNIQUE (token),

    CONSTRAINT fk_invitation_organization
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id),

    CONSTRAINT fk_invitation_invited_by
        FOREIGN KEY (invited_by)
        REFERENCES users(id),

    CONSTRAINT chk_invitation_role
        CHECK (
            role IN (
                'OWNER',
                'ADMIN',
                'DEVELOPER',
                'VIEWER'
            )
        ),

    CONSTRAINT chk_invitation_status
        CHECK (
            status IN (
                'PENDING',
                'ACCEPTED',
                'REJECTED',
                'EXPIRED',
                'CANCELLED'
            )
        )
);

CREATE INDEX idx_org_invitation_token
    ON organization_invitations(token);

CREATE INDEX idx_org_invitation_email
    ON organization_invitations(email);

CREATE INDEX idx_org_invitation_organization
    ON organization_invitations(organization_id);
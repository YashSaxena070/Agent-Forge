package com.agentforge.backend.organization.exception;

public class OrganizationAccessDeniedException
        extends RuntimeException {

    public OrganizationAccessDeniedException(
            String message
    ) {
        super(message);
    }
}
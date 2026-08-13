package com.agentforge.backend.organization.exception;

public class InvitationNotFoundException
        extends RuntimeException {

    public InvitationNotFoundException(
            String message
    ) {
        super(message);
    }
}
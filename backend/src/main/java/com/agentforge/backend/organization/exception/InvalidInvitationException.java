package com.agentforge.backend.organization.exception;

public class InvalidInvitationException
        extends RuntimeException {

    public InvalidInvitationException(
            String message
    ) {
        super(message);
    }
}
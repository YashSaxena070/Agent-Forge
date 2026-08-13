package com.agentforge.backend.organization.exception;

public class MemberAlreadyExistsException
        extends RuntimeException {

    public MemberAlreadyExistsException(
            String message
    ) {
        super(message);
    }
}
package com.agentforge.backend.project.exception;

public class ProjectNotFoundException
        extends RuntimeException {

    public ProjectNotFoundException(
            String message
    ) {
        super(message);
    }
}
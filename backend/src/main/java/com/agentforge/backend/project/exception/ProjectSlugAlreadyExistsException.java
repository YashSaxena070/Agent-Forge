package com.agentforge.backend.project.exception;

public class ProjectSlugAlreadyExistsException extends RuntimeException{

    public ProjectSlugAlreadyExistsException(String message){
        super(message);
    }
}

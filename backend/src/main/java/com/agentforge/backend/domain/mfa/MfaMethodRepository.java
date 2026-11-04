package com.agentforge.backend.domain.mfa;

import com.agentforge.backend.domain.user.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface MfaMethodRepository extends JpaRepository<MfaMethod, UUID> {

    List<MfaMethod> findByUser(User user);

    List<MfaMethod> findByUserAndStatus(User user, MfaStatus status);

    List<MfaMethod> findAllByUserAndMethodTypeAndStatus(
            User user, MfaType type, MfaStatus status);

    Optional<MfaMethod> findByUserAndMethodTypeAndStatus(
            User user, MfaType type, MfaStatus status);

    Optional<MfaMethod> findByCredentialId(String credentialId);

    @Query("SELECT m FROM MfaMethod m WHERE m.user = :user AND m.methodType = :type AND m.status = :status")
    List<MfaMethod> findByUserAndMethodTypeAndStatusNative(
            @Param("user") User user,
            @Param("type") MfaType type,
            @Param("status") MfaStatus status);
}
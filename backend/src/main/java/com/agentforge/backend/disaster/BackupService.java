package com.agentforge.backend.disaster;

import com.agentforge.backend.audit.AuditService;
import com.agentforge.backend.audit.AuditService.AuditEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.zip.GZIPOutputStream;
import java.util.zip.GZIPInputStream;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
@RequiredArgsConstructor
@Slf4j
public class BackupService {

    private final AuditService auditService;

    @Value("${backup.directory:/backups}")
    private String backupDirectory;

    @Value("${backup.retention-days:30}")
    private int retentionDays;

    @Value("${database.url}")
    private String databaseUrl;

    @Value("${database.username}")
    private String dbUsername;

    @Value("${database.password}")
    private String dbPassword;

    public CompletableFuture<BackupResult> createFullBackup() {
        return CompletableFuture.supplyAsync(() -> {
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
            String backupName = "full_backup_" + timestamp;
            Path backupPath = Paths.get(backupDirectory, backupName);

            try {
                Files.createDirectories(backupPath);

                // Run pg_dump
                ProcessBuilder pb = new ProcessBuilder(
                        "pg_dump",
                        "--no-owner",
                        "--no-privileges",
                        "--format=custom",
                        "--compress=9",
                        "--file=" + backupPath.resolve("database.dump").toString(),
                        databaseUrl
                );
                pb.environment().put("PGPASSWORD", dbPassword);
                Process process = pb.start();
                int exitCode = process.waitFor();

                if (exitCode != 0) {
                    String error = new String(process.getErrorStream().readAllBytes());
                    throw new IOException("pg_dump failed: " + error);
                }

                // Compress
                Path compressedFile = backupPath.resolve("database.dump.gz");
                compressFile(backupPath.resolve("database.dump").toFile(), compressedFile.toFile());

                // Calculate checksum
                String checksum = calculateChecksum(compressedFile.toFile());

                // Create manifest
                BackupManifest manifest = new BackupManifest(
                        "full",
                        LocalDateTime.now(),
                        compressedFile.toString(),
                        Files.size(compressedFile),
                        checksum,
                        "1.0"
                );
                writeManifest(backupPath, manifest);

                // Cleanup old backups
                cleanupOldBackups();

                return new BackupResult(true, backupName, compressedFile.toString(), 
                        Files.size(compressedFile), checksum, null);
            } catch (Exception e) {
                return new BackupResult(false, null, null, 0, null, e.getMessage());
            }
        });
    }

    public CompletableFuture<RestoreResult> restoreFromBackup(String backupName, String targetDatabase) {
        return CompletableFuture.supplyAsync(() -> {
            Path backupPath = Paths.get(backupDirectory, backupName);
            Path dumpFile = backupPath.resolve("database.dump.gz");

            if (!Files.exists(dumpFile)) {
                return new RestoreResult(false, "Backup file not found");
            }

            try {
                // Decompress
                Path decompressed = Files.createTempFile("restore_", ".dump");
                decompressFile(backupPath.resolve("database.dump.gz").toFile(), decompressed.toFile());

                // Verify checksum
                String checksum = calculateChecksum(backupPath.resolve("database.dump.gz").toFile());
                // Verify against manifest

                // Run pg_restore
                ProcessBuilder pb = new ProcessBuilder(
                        "pg_restore",
                        "--clean",
                        "--if-exists",
                        "--no-owner",
                        "--no-privileges",
                        "--dbname=" + targetDatabase,
                        decompressed.toString()
                );
                Process process = pb.start();
                int exitCode = process.waitFor();

                Files.deleteIfExists(decompressed);

                if (exitCode != 0) {
                    String error = new String(process.getErrorStream().readAllBytes());
                    return new RestoreResult(false, "pg_restore failed: " + error);
                }

                return new RestoreResult(true, "Restore completed successfully");
            } catch (Exception e) {
                return new RestoreResult(false, e.getMessage());
            }
        });
    }

    private void compressFile(File input, File output) throws IOException {
        try (FileInputStream fis = new FileInputStream(input);
             FileOutputStream fos = new FileOutputStream(output);
             GZIPOutputStream gos = new GZIPOutputStream(fos)) {
            byte[] buffer = new byte[8192];
            int len;
            while ((len = fis.read(buffer)) > 0) {
                gos.write(buffer, 0, len);
            }
        }
    }

    private void decompressFile(File input, File output) throws IOException {
        try (GZIPInputStream gis = new GZIPInputStream(new FileInputStream(input));
             FileOutputStream fos = new FileOutputStream(output)) {
            byte[] buffer = new byte[8192];
            int len;
            while ((len = gis.read(buffer)) > 0) {
                fos.write(buffer, 0, len);
            }
        }
    }

    private String calculateChecksum(File file) throws IOException {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            try (FileInputStream fis = new FileInputStream(file)) {
                byte[] buffer = new byte[8192];
                int len;
                while ((len = fis.read(buffer)) > 0) {
                    digest.update(buffer, 0, len);
                }
            }
            return Base64.getEncoder().encodeToString(digest.digest());
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException("SHA-256 not available", e);
        }
    }

    private void writeManifest(Path backupPath, BackupManifest manifest) throws IOException {
        Path manifestFile = backupPath.resolve("manifest.json");
        String json = new ObjectMapper().writeValueAsString(manifest);
        Files.writeString(manifestFile, json);
    }

    private void cleanupOldBackups() throws IOException {
        Path dir = Paths.get(backupDirectory);
        if (!Files.exists(dir)) return;

        LocalDateTime cutoff = LocalDateTime.now().minusDays(retentionDays);
        
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
            for (Path entry : stream) {
                if (Files.isDirectory(entry)) {
                    String name = entry.getFileName().toString();
                    if (name.startsWith("full_backup_")) {
                        try {
                            String timestampStr = name.substring("full_backup_".length());
                            LocalDateTime backupTime = LocalDateTime.parse(timestampStr, 
                                    DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
                            if (backupTime.isBefore(cutoff)) {
                                deleteDirectory(entry);
                            }
                        } catch (Exception ignored) {
                        }
                    }
                }
            }
        }
    }

    private void deleteDirectory(Path path) throws IOException {
        Files.walk(path)
                .sorted(Comparator.reverseOrder())
                .forEach(p -> {
                    try {
                        Files.delete(p);
                    } catch (IOException ignored) {}
                });
    }

    record BackupManifest(
            String type,
            LocalDateTime timestamp,
            String file,
            long sizeBytes,
            String checksum,
            String schemaVersion
    ) {}

    record BackupResult(
            boolean success,
            String backupName,
            String filePath,
            long sizeBytes,
            String checksum,
            String error
    ) {}

    record RestoreResult(
            boolean success,
            String message
    ) {}
}
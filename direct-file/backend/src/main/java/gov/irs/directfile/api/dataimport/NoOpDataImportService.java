package gov.irs.directfile.api.dataimport;

import java.util.Collections;
import java.util.Date;
import java.util.UUID;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

import gov.irs.directfile.api.dataimport.model.WrappedPopulatedData;

@Slf4j
@Service
@Profile("!mock")
public class NoOpDataImportService implements DataImportService {

    @Override
    public void sendPreFetchRequest(UUID taxReturnId, UUID userId, UUID externalId, String tin, int taxYear) {
        log.info(
                "No data import provider configured; skipping prefetch for taxReturnId={}, userId={}, externalId={}",
                taxReturnId,
                userId,
                externalId);
    }

    @Override
    public WrappedPopulatedData getPopulatedData(UUID taxReturnId, UUID userId, Date taxReturnCreatedAt) {
        Date createdAt = taxReturnCreatedAt != null ? taxReturnCreatedAt : new Date();
        log.info(
                "No data import provider configured; returning empty populated data for taxReturnId={}, userId={}",
                taxReturnId,
                userId);
        return WrappedPopulatedData.from(Collections.emptyList(), createdAt);
    }
}

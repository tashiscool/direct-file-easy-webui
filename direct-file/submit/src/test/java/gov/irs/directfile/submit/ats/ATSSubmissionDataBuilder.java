package gov.irs.directfile.submit.ats;

import gov.irs.directfile.submit.domain.UserContextData;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Builder utility for creating MeF submission data from ATS scenario information.
 *
 * This class provides methods to:
 * - Generate submission IDs
 * - Create UserContextData objects
 * - Format values for MeF XML output
 */
public class ATSSubmissionDataBuilder {

    private static final AtomicInteger sequenceCounter = new AtomicInteger(1);
    private static final String DEFAULT_EFIN = "123456";

    /**
     * Build UserContextData for an ATS scenario.
     *
     * @param scenarioId The ATS scenario identifier
     * @param userTin The taxpayer's TIN (SSN or ITIN)
     * @param tinType The type of TIN ("SSN" or "ITIN")
     * @return Configured UserContextData
     */
    public UserContextData buildUserContext(String scenarioId, String userTin, String tinType) {
        String submissionId = generateSubmissionId(DEFAULT_EFIN, sequenceCounter.getAndIncrement());
        String taxReturnId = UUID.randomUUID().toString();
        String userId = UUID.randomUUID().toString();

        return new UserContextData(
            submissionId,
            userId,
            taxReturnId,
            userTin,
            tinType,
            "127.0.0.1", // remoteAddress for testing
            LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        );
    }

    /**
     * Generate a MeF-compliant 20-character submission ID.
     *
     * Format: EFIN (6) + Year (4) + Julian Day (3) + Time component (7)
     *
     * @param efin The EFIN (6 digits)
     * @param sequence Sequence number for uniqueness
     * @return 20-character submission ID
     */
    public String generateSubmissionId(String efin, int sequence) {
        LocalDateTime now = LocalDateTime.now();
        int year = now.getYear();
        int dayOfYear = now.getDayOfYear();
        int timeComponent = now.getHour() * 10000 + now.getMinute() * 100 + now.getSecond();

        // Ensure EFIN is 6 characters
        String paddedEfin = String.format("%6s", efin).replace(' ', '0');

        // Build submission ID: EFIN(6) + Year(4) + JulianDay(3) + Time(5) + Seq(2)
        return String.format("%s%04d%03d%05d%02d",
            paddedEfin,
            year,
            dayOfYear,
            timeComponent % 100000,
            sequence % 100
        );
    }

    /**
     * Map filing status code to MeF value.
     *
     * @param filingStatus The filing status code (1-5)
     * @return MeF filing status code as string
     */
    public String mapFilingStatusToMeF(int filingStatus) {
        return String.valueOf(filingStatus);
    }

    /**
     * Format dollar amount for MeF XML (rounded to whole dollars).
     *
     * @param amount The dollar amount
     * @return Formatted string (whole dollars, no cents)
     */
    public String formatAmount(BigDecimal amount) {
        if (amount == null) {
            return "0";
        }
        return amount.setScale(0, RoundingMode.HALF_UP).toPlainString();
    }

    /**
     * Format dollar amount with cents for MeF XML.
     *
     * @param amount The dollar amount
     * @return Formatted string with 2 decimal places
     */
    public String formatAmountWithCents(BigDecimal amount) {
        if (amount == null) {
            return "0.00";
        }
        return amount.setScale(2, RoundingMode.HALF_UP).toPlainString();
    }

    /**
     * Format SSN by removing dashes.
     *
     * @param ssn The SSN (with or without dashes)
     * @return 9-digit SSN without dashes
     */
    public String formatSsn(String ssn) {
        if (ssn == null) {
            return null;
        }
        return ssn.replace("-", "");
    }

    /**
     * Format EIN by removing dashes.
     *
     * @param ein The EIN (with or without dashes)
     * @return 9-digit EIN without dashes
     */
    public String formatEin(String ein) {
        if (ein == null) {
            return null;
        }
        return ein.replace("-", "");
    }

    /**
     * Format date for MeF XML.
     *
     * @param year The year
     * @param month The month (1-12)
     * @param day The day (1-31)
     * @return Date in YYYY-MM-DD format
     */
    public String formatDate(int year, int month, int day) {
        return String.format("%04d-%02d-%02d", year, month, day);
    }

    /**
     * Escape special characters for XML content.
     *
     * @param value The raw string value
     * @return XML-safe escaped string
     */
    public String escapeXml(String value) {
        if (value == null) {
            return null;
        }
        return value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\"", "&quot;")
            .replace("'", "&apos;");
    }

    /**
     * Build MeF return type code.
     *
     * @param formType The form type (1040, 1040-NR, 1040-SS, etc.)
     * @return MeF return type code
     */
    public String buildReturnTypeCd(String formType) {
        switch (formType) {
            case "1040":
                return "1040";
            case "1040-SR":
                return "1040SR";
            case "1040-NR":
                return "1040NR";
            case "1040-SS":
                return "1040SS";
            case "4868":
                return "4868";
            default:
                return "1040";
        }
    }

    /**
     * Create a simple MeF submission manifest XML snippet.
     *
     * @param submissionId The submission ID
     * @param returnTypeCd The return type code
     * @param taxYear The tax year
     * @return Manifest XML string
     */
    public String buildManifestXml(String submissionId, String returnTypeCd, int taxYear) {
        return String.format(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" +
            "<SubmissionManifest xmlns=\"http://www.irs.gov/efile\">" +
            "<SubmissionId>%s</SubmissionId>" +
            "<TaxYear>%d</TaxYear>" +
            "<ReturnTypeCd>%s</ReturnTypeCd>" +
            "</SubmissionManifest>",
            submissionId,
            taxYear,
            returnTypeCd
        );
    }
}

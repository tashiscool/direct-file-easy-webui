package gov.irs.directfile.api.ats;

import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.api.loaders.service.FactGraphService;
import gov.irs.directfile.api.util.base.BaseIntegrationTest;
import gov.irs.directfile.models.FactTypeWithItem;
import gov.irs.factgraph.Graph;
import gov.irs.factgraph.monads.Result;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.annotation.DirtiesContext;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
@DirtiesContext(classMode = DirtiesContext.ClassMode.AFTER_CLASS)
public class SelectedFormParityExportTest extends BaseIntegrationTest {

    @Autowired
    private FactGraphService factGraphService;

    @DynamicPropertySource
    static void registerDataSourceProperties(DynamicPropertyRegistry registry) {
        String dbUrl = buildTestDbUrl("selected-form-parity");
        registry.add("spring.datasource.url", () -> dbUrl);
        registry.add("spring.liquibase.url", () -> dbUrl);
        registry.add("spring.datasource.username", () -> "sa");
        registry.add("spring.datasource.password", () -> "");
        registry.add("spring.liquibase.user", () -> "sa");
        registry.add("spring.liquibase.password", () -> "");
    }

    @Test
    @DisplayName("Exports targeted Direct File outputs for cross-engine parity comparison")
    void exportSelectedFormOutputs() throws IOException {
        ATSToFactGraphConverter converter = new ATSToFactGraphConverter();
        Map<String, Map<String, Object>> export = new LinkedHashMap<>();

        export.put("scenario-28-taylor-qbi.json", extractQbiFacts(converter, "scenario-28-taylor-qbi.json"));
        export.put("scenario-18-thompson-rental-qbi-overflow", extractQbiOverflowFacts(converter));
        export.put("scenario-18-thompson-rental.json", extractScheduleEFacts(converter, "scenario-18-thompson-rental.json"));
        export.put("scenario-29-white-k1.json", extractScheduleEFacts(converter, "scenario-29-white-k1.json"));
        export.put("scenario-nr2-desilva.json", extract1040NrFacts(converter, "scenario-nr2-desilva.json"));
        export.put("scenario-nr5-chen.json", extract1040NrFacts(converter, "scenario-nr5-chen.json"));
        export.put("scenario-nr12-harrier.json", extract1040NrFacts(converter, "scenario-nr12-harrier.json"));

        Path exportPath = Path.of(System.getProperty(
            "parity.export.path",
            "target/parity-reports/direct-file-selected-form-outputs.json"
        ));
        Files.createDirectories(exportPath.getParent());

        ObjectMapper mapper = new ObjectMapper().enable(SerializationFeature.INDENT_OUTPUT);
        mapper.writeValue(exportPath.toFile(), export);

        assertThat(Files.exists(exportPath)).isTrue();
    }

    private Map<String, Object> extractQbiFacts(ATSToFactGraphConverter converter, String scenarioFileName) throws IOException {
        Graph graph = graphForScenario(converter, scenarioFileName);
        Map<String, Object> facts = new LinkedHashMap<>();
        facts.put("scenario", scenarioFileName);
        facts.put("directQBI", getFactAsBigDecimal(graph, "/directQBI"));
        facts.put("totalQBI", getFactAsBigDecimal(graph, "/totalQBI"));
        facts.put("qbiDeduction", getFactAsBigDecimal(graph, "/qbiDeduction"));
        facts.put("qbi8995A", getFactAsBigDecimal(graph, "/qbi8995A"));
        facts.put("w2Wages8995A", getFactAsBigDecimal(graph, "/w2Wages8995A"));
        facts.put("ubia8995A", getFactAsBigDecimal(graph, "/ubia8995A"));
        facts.put("qbiComponentBeforeLimitation", getFactAsBigDecimal(graph, "/qbiComponentBeforeLimitation"));
        facts.put("qbiComponentAfter8995A", getFactAsBigDecimal(graph, "/qbiComponentAfter8995A"));
        facts.put("w2UBIALimit8995A", getFactAsBigDecimal(graph, "/w2UBIALimit8995A"));
        facts.put("isSSTB8995A", getFactAsBoolean(graph, "/isSSTB8995A"));
        facts.put("form8995ATotalBusinesses", getFactAsInt(graph, "/form8995ATotalBusinesses"));
        facts.put("form8995AOverflowBusinesses", getFactAsInt(graph, "/form8995AOverflowBusinesses"));
        facts.put("hasForm8995AAttachmentStatement", getFactAsBoolean(graph, "/hasForm8995AAttachmentStatement"));
        facts.put("form8995AOverflowQBI", getFactAsBigDecimal(graph, "/form8995AOverflowQBI"));
        facts.put("form8995AOverflowW2Wages", getFactAsBigDecimal(graph, "/form8995AOverflowW2Wages"));
        facts.put("form8995AOverflowUBIA", getFactAsBigDecimal(graph, "/form8995AOverflowUBIA"));
        facts.put("form8995AOverflowPatronReduction", getFactAsBigDecimal(graph, "/form8995AOverflowPatronReduction"));
        facts.put("reitDividends", getFactAsBigDecimal(graph, "/reitDividends"));
        facts.put("ptpIncome", getFactAsBigDecimal(graph, "/ptpIncome"));
        return facts;
    }

    private Map<String, Object> extractQbiOverflowFacts(ATSToFactGraphConverter converter) throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario("scenario-18-thompson-rental.json");
        Map<String, Object> form8995Qbi = new HashMap<>();
        form8995Qbi.put("businesses", List.of(
            qbiBusiness("Alpha Advisory", "210000", "60000", "100000", false),
            qbiBusiness("Beta Logistics", "90000", "20000", "50000", false),
            qbiBusiness("Gamma Studio", "50000", "10000", "20000", true),
            qbiBusiness("Delta Rentals", "40000", "5000", "15000", false),
            qbiBusiness("Echo Foods", "30000", "3000", "10000", false),
            qbiBusiness("Foxtrot Labs", "25000", "4000", "8000", true),
            qbiBusiness("Gaia Farms", "15000", "2000", "6000", false)
        ));
        scenario.setForm8995QBI(form8995Qbi);
        Graph graph = factGraphService.getGraph(converter.convert(scenario));

        Map<String, Object> facts = new LinkedHashMap<>();
        facts.put("scenario", "scenario-18-thompson-rental-qbi-overflow");
        facts.put("form8995ATotalBusinesses", getFactAsInt(graph, "/form8995ATotalBusinesses"));
        facts.put("form8995AOverflowBusinesses", getFactAsInt(graph, "/form8995AOverflowBusinesses"));
        facts.put("hasForm8995AAttachmentStatement", getFactAsBoolean(graph, "/hasForm8995AAttachmentStatement"));
        facts.put("form8995ABusiness4Name", getFactAsString(graph, "/form8995ABusiness4Name"));
        facts.put("form8995ABusiness5Name", getFactAsString(graph, "/form8995ABusiness5Name"));
        facts.put("form8995ABusiness6Name", getFactAsString(graph, "/form8995ABusiness6Name"));
        facts.put("form8995ABusiness7Name", getFactAsString(graph, "/form8995ABusiness7Name"));
        facts.put("form8995ABusiness4QBI", getFactAsBigDecimal(graph, "/form8995ABusiness4QBI"));
        facts.put("form8995ABusiness5QBI", getFactAsBigDecimal(graph, "/form8995ABusiness5QBI"));
        facts.put("form8995ABusiness6QBI", getFactAsBigDecimal(graph, "/form8995ABusiness6QBI"));
        facts.put("form8995ABusiness7QBI", getFactAsBigDecimal(graph, "/form8995ABusiness7QBI"));
        facts.put("form8995ABusiness4W2Wages", getFactAsBigDecimal(graph, "/form8995ABusiness4W2Wages"));
        facts.put("form8995ABusiness5W2Wages", getFactAsBigDecimal(graph, "/form8995ABusiness5W2Wages"));
        facts.put("form8995ABusiness6W2Wages", getFactAsBigDecimal(graph, "/form8995ABusiness6W2Wages"));
        facts.put("form8995ABusiness7W2Wages", getFactAsBigDecimal(graph, "/form8995ABusiness7W2Wages"));
        facts.put("form8995ABusiness4UBIA", getFactAsBigDecimal(graph, "/form8995ABusiness4UBIA"));
        facts.put("form8995ABusiness5UBIA", getFactAsBigDecimal(graph, "/form8995ABusiness5UBIA"));
        facts.put("form8995ABusiness6UBIA", getFactAsBigDecimal(graph, "/form8995ABusiness6UBIA"));
        facts.put("form8995ABusiness7UBIA", getFactAsBigDecimal(graph, "/form8995ABusiness7UBIA"));
        facts.put("form8995ABusiness3IsSSTB", getFactAsBoolean(graph, "/form8995ABusiness3IsSSTB"));
        facts.put("form8995ABusiness4IsSSTB", getFactAsBoolean(graph, "/form8995ABusiness4IsSSTB"));
        facts.put("form8995ABusiness5IsSSTB", getFactAsBoolean(graph, "/form8995ABusiness5IsSSTB"));
        facts.put("form8995ABusiness6IsSSTB", getFactAsBoolean(graph, "/form8995ABusiness6IsSSTB"));
        facts.put("form8995ABusiness7IsSSTB", getFactAsBoolean(graph, "/form8995ABusiness7IsSSTB"));
        facts.put("form8995AOverflowQBI", getFactAsBigDecimal(graph, "/form8995AOverflowQBI"));
        facts.put("form8995AOverflowW2Wages", getFactAsBigDecimal(graph, "/form8995AOverflowW2Wages"));
        facts.put("form8995AOverflowUBIA", getFactAsBigDecimal(graph, "/form8995AOverflowUBIA"));
        return facts;
    }

    private Map<String, Object> extractScheduleEFacts(ATSToFactGraphConverter converter, String scenarioFileName) throws IOException {
        Graph graph = graphForScenario(converter, scenarioFileName);
        Map<String, Object> facts = new LinkedHashMap<>();
        facts.put("scenario", scenarioFileName);
        facts.put("hasRentalIncome", getFactAsBoolean(graph, "/hasRentalIncome"));
        facts.put("hasScheduleEPage2Activity", getFactAsBoolean(graph, "/hasScheduleEPage2Activity"));
        facts.put("totalRentalRoyaltyIncome", getFactAsBigDecimal(graph, "/totalRentalRoyaltyIncome"));
        facts.put("totalRentalExpenses", getFactAsBigDecimal(graph, "/totalRentalExpenses"));
        facts.put("rentalNetIncomeLoss", getFactAsBigDecimal(graph, "/rentalNetIncomeLoss"));
        facts.put("partnershipScheduleEIncome", getFactAsBigDecimal(graph, "/partnershipScheduleEIncome"));
        facts.put("scheduleEPage2IncomeLoss", getFactAsBigDecimal(graph, "/scheduleEPage2IncomeLoss"));
        facts.put("scheduleEQualifiedBusinessIncome", getFactAsBigDecimal(graph, "/scheduleEQualifiedBusinessIncome"));
        facts.put("scheduleETotalIncomeLoss", getFactAsBigDecimal(graph, "/scheduleETotalIncomeLoss"));
        return facts;
    }

    private Map<String, Object> extract1040NrFacts(ATSToFactGraphConverter converter, String scenarioFileName) throws IOException {
        Graph graph = graphForScenario(converter, scenarioFileName);
        Map<String, Object> facts = new LinkedHashMap<>();
        facts.put("scenario", scenarioFileName);
        facts.put("hasScheduleOI", getFactAsBoolean(graph, "/hasScheduleOI"));
        facts.put("hasScheduleNEC", getFactAsBoolean(graph, "/hasScheduleNEC"));
        facts.put("countryOfCitizenship", getFactAsString(graph, "/countryOfCitizenship"));
        facts.put("countryOfResidence", getFactAsString(graph, "/countryOfResidence"));
        facts.put("visaType", getFactAsString(graph, "/visaType"));
        facts.put("daysInUS", getFactAsInt(graph, "/daysInUS"));
        facts.put("daysInUSPriorYear", getFactAsInt(graph, "/daysInUSPriorYear"));
        facts.put("daysInUSTwoYearsPrior", getFactAsInt(graph, "/daysInUSTwoYearsPrior"));
        facts.put("substantialPresenceWeightedDays", getFactAsInt(graph, "/substantialPresenceWeightedDays"));
        facts.put("claimsTreatyBenefits", getFactAsBoolean(graph, "/claimsTreatyBenefits"));
        facts.put("scheduleOIRequiresTreatyDisclosure", getFactAsBoolean(graph, "/scheduleOIRequiresTreatyDisclosure"));
        facts.put("scheduleOIHasForeignAddress", getFactAsBoolean(graph, "/scheduleOIHasForeignAddress"));
        facts.put("treatyCountry", getFactAsString(graph, "/treatyCountry"));
        facts.put("treatyArticle", getFactAsString(graph, "/treatyArticle"));
        facts.put("treatyBenefitDescription", getFactAsString(graph, "/treatyBenefitDescription"));
        facts.put("reducedTreatyRate", getFactAsBigDecimal(graph, "/reducedTreatyRate"));
        facts.put("dividendsFDAPRate", getFactAsBigDecimal(graph, "/dividendsFDAPRate"));
        facts.put("interestFDAPRate", getFactAsBigDecimal(graph, "/interestFDAPRate"));
        facts.put("royaltiesFDAPRate", getFactAsBigDecimal(graph, "/royaltiesFDAPRate"));
        facts.put("otherFDAPRate", getFactAsBigDecimal(graph, "/otherFDAPRate"));
        facts.put("otherFDAPDescription", getFactAsString(graph, "/otherFDAPDescription"));
        facts.put("scheduleNECLineItemCount", getFactAsInt(graph, "/scheduleNECLineItemCount"));
        facts.put("totalECI", getFactAsBigDecimal(graph, "/totalECI"));
        facts.put("totalFDAPIncome", getFactAsBigDecimal(graph, "/totalFDAPIncome"));
        facts.put("taxOnECI", getFactAsBigDecimal(graph, "/taxOnECI"));
        facts.put("scheduleNECTax", getFactAsBigDecimal(graph, "/scheduleNECTax"));
        facts.put("dividendsFDAPTax", getFactAsBigDecimal(graph, "/dividendsFDAPTax"));
        facts.put("interestFDAPTax", getFactAsBigDecimal(graph, "/interestFDAPTax"));
        facts.put("royaltiesFDAPTax", getFactAsBigDecimal(graph, "/royaltiesFDAPTax"));
        facts.put("otherFDAPTax", getFactAsBigDecimal(graph, "/otherFDAPTax"));
        facts.put("totalTaxNR", getFactAsBigDecimal(graph, "/totalTaxNR"));
        return facts;
    }

    private Map<String, Object> qbiBusiness(
        String businessName,
        String qbi,
        String w2Wages,
        String ubia,
        boolean isSstb
    ) {
        Map<String, Object> business = new HashMap<>();
        business.put("businessName", businessName);
        business.put("qualifiedBusinessIncome", new BigDecimal(qbi));
        business.put("w2Wages", new BigDecimal(w2Wages));
        business.put("ubia", new BigDecimal(ubia));
        business.put("isSpecifiedServiceBusiness", isSstb);
        return business;
    }

    private Graph graphForScenario(ATSToFactGraphConverter converter, String scenarioFileName) throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario(scenarioFileName);
        Map<String, FactTypeWithItem> facts = converter.convert(scenario);
        return factGraphService.getGraph(facts);
    }

    private BigDecimal getFactAsBigDecimal(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue() && result.get() != null) {
                BigDecimal parsed = parseDecimalValue(result.get());
                if (parsed != null) {
                    return parsed.setScale(2, RoundingMode.HALF_UP);
                }
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
    }

    private BigDecimal parseDecimalValue(Object value) {
        if (value == null) {
            return null;
        }
        if (value instanceof scala.math.BigDecimal) {
            return new BigDecimal(value.toString());
        }
        if (value instanceof BigDecimal bigDecimal) {
            return bigDecimal;
        }
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue());
        }
        if (value instanceof java.util.Map<?, ?> map) {
            Object numerator = map.get("n");
            Object denominator = map.get("d");
            if (numerator instanceof Number n && denominator instanceof Number d && d.doubleValue() != 0d) {
                return BigDecimal.valueOf(n.doubleValue())
                    .divide(BigDecimal.valueOf(d.doubleValue()), 8, RoundingMode.HALF_UP);
            }
        }
        if (value instanceof com.fasterxml.jackson.databind.JsonNode node
            && node.has("n") && node.has("d") && node.get("d").asDouble() != 0d) {
            return BigDecimal.valueOf(node.get("n").asDouble())
                .divide(BigDecimal.valueOf(node.get("d").asDouble()), 8, RoundingMode.HALF_UP);
        }
        try {
            java.lang.reflect.Method numeratorMethod = value.getClass().getMethod("numerator");
            java.lang.reflect.Method denominatorMethod = value.getClass().getMethod("denominator");
            Object numerator = numeratorMethod.invoke(value);
            Object denominator = denominatorMethod.invoke(value);
            if (numerator instanceof Number n && denominator instanceof Number d && d.doubleValue() != 0d) {
                return BigDecimal.valueOf(n.doubleValue())
                    .divide(BigDecimal.valueOf(d.doubleValue()), 8, RoundingMode.HALF_UP);
            }
        } catch (ReflectiveOperationException ignored) {
            // Fall through to string parsing.
        }
        String text = value.toString();
        java.util.regex.Matcher jsonMatcher =
            java.util.regex.Pattern.compile(".*[\\{\\(]\\s*\\\"?n\\\"?\\s*[:=]\\s*([0-9.-]+).*\\\"?d\\\"?\\s*[:=]\\s*([0-9.-]+).*")
                .matcher(text);
        if (jsonMatcher.matches()) {
            BigDecimal denominator = new BigDecimal(jsonMatcher.group(2));
            if (denominator.compareTo(BigDecimal.ZERO) != 0) {
                return new BigDecimal(jsonMatcher.group(1))
                    .divide(denominator, 8, RoundingMode.HALF_UP);
            }
        }
        return new BigDecimal(text);
    }

    private Integer getFactAsInt(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue() && result.get() != null) {
                Object value = result.get();
                if (value instanceof Number number) {
                    return number.intValue();
                }
                return Integer.parseInt(value.toString());
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
    }

    private Boolean getFactAsBoolean(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue() && result.get() != null) {
                Object value = result.get();
                if (value instanceof Boolean bool) {
                    return bool;
                }
                return Boolean.valueOf(value.toString());
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
    }

    private String getFactAsString(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue() && result.get() != null) {
                return result.get().toString();
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
    }

    private static String buildTestDbUrl(String prefix) {
        return "jdbc:h2:mem:" + prefix + "_" + UUID.randomUUID().toString().replace("-", "")
            + ";DB_CLOSE_DELAY=-1;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DEFAULT_NULL_ORDERING=HIGH";
    }
}

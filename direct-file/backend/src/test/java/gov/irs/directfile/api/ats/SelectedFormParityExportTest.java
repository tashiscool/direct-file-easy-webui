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
        facts.put("form8995ATotalBusinesses", getFactAsInt(graph, "/form8995ATotalBusinesses"));
        facts.put("form8995AOverflowBusinesses", getFactAsInt(graph, "/form8995AOverflowBusinesses"));
        facts.put("hasForm8995AAttachmentStatement", getFactAsBoolean(graph, "/hasForm8995AAttachmentStatement"));
        facts.put("form8995AOverflowQBI", getFactAsBigDecimal(graph, "/form8995AOverflowQBI"));
        facts.put("reitDividends", getFactAsBigDecimal(graph, "/reitDividends"));
        facts.put("ptpIncome", getFactAsBigDecimal(graph, "/ptpIncome"));
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
        facts.put("totalECI", getFactAsBigDecimal(graph, "/totalECI"));
        facts.put("totalFDAPIncome", getFactAsBigDecimal(graph, "/totalFDAPIncome"));
        facts.put("taxOnECI", getFactAsBigDecimal(graph, "/taxOnECI"));
        facts.put("scheduleNECTax", getFactAsBigDecimal(graph, "/scheduleNECTax"));
        facts.put("totalTaxNR", getFactAsBigDecimal(graph, "/totalTaxNR"));
        return facts;
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
                return new BigDecimal(result.get().toString()).setScale(2, RoundingMode.HALF_UP);
            }
        } catch (Exception ignored) {
            return null;
        }
        return null;
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

package gov.irs.directfile.api.ats;

import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import gov.irs.directfile.api.ats.converter.ATSToFactGraphConverter;
import gov.irs.directfile.api.ats.model.ATSScenarioData;
import gov.irs.directfile.api.loaders.service.FactGraphService;
import gov.irs.directfile.api.util.base.BaseIntegrationTest;
import gov.irs.directfile.models.FactTypeWithItem;
import gov.irs.factgraph.Graph;
import gov.irs.factgraph.monads.Result;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.io.IOException;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@ActiveProfiles("test")
public class TaxYear2025RegressionTest extends BaseIntegrationTest {

    private static final String BOOLEAN_WRAPPER = "gov.irs.factgraph.persisters.BooleanWrapper";
    private static final String DOLLAR_WRAPPER = "gov.irs.factgraph.persisters.DollarWrapper";

    @Autowired
    private FactGraphService factGraphService;

    private ATSToFactGraphConverter converter;
    private JsonNodeFactory nodeFactory;

    @BeforeEach
    void setUp() {
        converter = new ATSToFactGraphConverter();
        nodeFactory = JsonNodeFactory.instance;
    }

    @Test
    @DisplayName("QBI thresholds use the published 2025 amounts and MFJ threshold selection")
    void testQbiThresholdsUsePublished2025Amounts() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-13-birch.json");
        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdSingle"))
            .isEqualByComparingTo(new BigDecimal("197300.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdMFJ"))
            .isEqualByComparingTo(new BigDecimal("394600.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdSingle8995A"))
            .isEqualByComparingTo(new BigDecimal("197300.00"));
        assertThat(getFactAsBigDecimal(graph, "/qbiThresholdMFJ8995A"))
            .isEqualByComparingTo(new BigDecimal("394600.00"));
        assertThat(getFactAsBoolean(graph, "/canUseSimplifiedMethod")).isTrue();
    }

    @Test
    @DisplayName("Schedule 1-A applies stepped overtime and tip phase-outs")
    void testSchedule1ASteppedOvertimeAndTipPhaseouts() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-13-birch.json");
        facts.put("/hasQualifiedOvertime", booleanWrapper(true));
        facts.put("/qualifiedOvertimeIncome", dollarWrapper("25000"));
        facts.put("/hasQualifiedTips", booleanWrapper(true));
        facts.put("/qualifiedTipIncome", dollarWrapper("25000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/overtimeDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
        assertThat(getFactAsBigDecimal(graph, "/tipDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("24000.00"));
    }

    @Test
    @DisplayName("Schedule 1-A disallows MFS wage deductions and senior bonus")
    void testSchedule1AMfsRestrictions() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-8-lewis.json");
        facts.put("/hasQualifiedOvertime", booleanWrapper(true));
        facts.put("/qualifiedOvertimeIncome", dollarWrapper("12500"));
        facts.put("/hasQualifiedTips", booleanWrapper(true));
        facts.put("/qualifiedTipIncome", dollarWrapper("25000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/overtimeDeductionAmount"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/tipDeductionAmount"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
        assertThat(getFactAsBigDecimal(graph, "/totalSeniorBonusDeduction"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));
    }

    @Test
    @DisplayName("Schedule 1-A auto loan phase-out rounds up each thousand dollars of excess income")
    void testSchedule1AAutoLoanRoundUpPhaseout() throws IOException {
        Map<String, FactTypeWithItem> facts = scenarioFacts("scenario-1-tara-black.json");
        distributeTotalWagesAcrossW2s(facts, new BigDecimal("100001"));
        facts.put("/vehicleIsDomesticManufacture", booleanWrapper(true));
        facts.put("/qualifiedAutoLoanInterest", dollarWrapper("1000"));

        Graph graph = factGraphService.getGraph(facts);

        assertThat(getFactAsBigDecimal(graph, "/autoLoanInterestDeductionAmount"))
            .isEqualByComparingTo(new BigDecimal("800.00"));
    }

    @Test
    @DisplayName("Form 4684 keeps the 10% AGI floor unless the loss is a qualified disaster loss")
    void testCasualtyLossQualifiedDisasterHandling() throws IOException {
        Map<String, FactTypeWithItem> ordinaryFacts = scenarioFacts("scenario-1-tara-black.json");
        ordinaryFacts.put("/hasCasualtyOrTheft", booleanWrapper(true));
        ordinaryFacts.put("/isInFederalDisasterArea", booleanWrapper(true));
        ordinaryFacts.put("/isQualifiedDisasterLoss", booleanWrapper(false));
        ordinaryFacts.put("/property1CostBasis", dollarWrapper("1000"));
        ordinaryFacts.put("/property1InsuranceReimbursement", dollarWrapper("0"));
        ordinaryFacts.put("/property1FMVBefore", dollarWrapper("1000"));
        ordinaryFacts.put("/property1FMVAfter", dollarWrapper("0"));

        Graph ordinaryGraph = factGraphService.getGraph(ordinaryFacts);
        assertThat(getFactAsBigDecimal(ordinaryGraph, "/deductibleCasualtyLoss"))
            .isEqualByComparingTo(BigDecimal.ZERO.setScale(2, RoundingMode.HALF_UP));

        Map<String, FactTypeWithItem> qualifiedFacts = new HashMap<>(ordinaryFacts);
        qualifiedFacts.put("/isQualifiedDisasterLoss", booleanWrapper(true));

        Graph qualifiedGraph = factGraphService.getGraph(qualifiedFacts);
        assertThat(getFactAsBigDecimal(qualifiedGraph, "/deductibleCasualtyLoss"))
            .isEqualByComparingTo(new BigDecimal("500.00"));
    }

    private Map<String, FactTypeWithItem> scenarioFacts(String scenarioFileName) throws IOException {
        ATSScenarioData scenario = ATSScenarioLoader.loadScenario(scenarioFileName);
        return new HashMap<>(converter.convert(scenario));
    }

    private void distributeTotalWagesAcrossW2s(Map<String, FactTypeWithItem> facts, BigDecimal totalWages) {
        List<String> wagePaths = facts.keySet().stream()
            .filter(path -> path.startsWith("/formW2s/#") && path.endsWith("/wages"))
            .sorted(Comparator.naturalOrder())
            .toList();

        assertThat(wagePaths).isNotEmpty();

        BigDecimal[] quotientAndRemainder = totalWages.divideAndRemainder(BigDecimal.valueOf(wagePaths.size()));
        BigDecimal evenShare = quotientAndRemainder[0];
        BigDecimal remainder = quotientAndRemainder[1];

        for (int i = 0; i < wagePaths.size(); i++) {
            String wagesPath = wagePaths.get(i);
            BigDecimal amount = evenShare;
            if (i == wagePaths.size() - 1) {
                amount = amount.add(remainder);
            }

            String basePath = wagesPath.substring(0, wagesPath.length() - "/wages".length());
            facts.put(basePath + "/wages", dollarWrapper(amount.toPlainString()));
            facts.put(basePath + "/socialSecurityWages", dollarWrapper(amount.toPlainString()));
            facts.put(basePath + "/medicareWagesAndTips", dollarWrapper(amount.toPlainString()));
            if (facts.containsKey(basePath + "/stateWages")) {
                facts.put(basePath + "/stateWages", dollarWrapper(amount.toPlainString()));
            }
        }
    }

    private FactTypeWithItem booleanWrapper(boolean value) {
        return new FactTypeWithItem(BOOLEAN_WRAPPER, BooleanNode.valueOf(value));
    }

    private FactTypeWithItem dollarWrapper(String value) {
        return new FactTypeWithItem(DOLLAR_WRAPPER, nodeFactory.textNode(value));
    }

    private Boolean getFactAsBoolean(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value instanceof Boolean) {
                    return (Boolean) value;
                }
                if (value != null) {
                    return Boolean.valueOf(value.toString());
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }

    private BigDecimal getFactAsBigDecimal(Graph graph, String path) {
        try {
            Result<Object> result = graph.get(path);
            if (result != null && result.hasValue()) {
                Object value = result.get();
                if (value instanceof scala.math.BigDecimal) {
                    return new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP);
                } else if (value instanceof BigDecimal) {
                    return ((BigDecimal) value).setScale(2, RoundingMode.HALF_UP);
                } else if (value instanceof Number) {
                    return BigDecimal.valueOf(((Number) value).doubleValue())
                        .setScale(2, RoundingMode.HALF_UP);
                } else if (value != null) {
                    return new BigDecimal(value.toString()).setScale(2, RoundingMode.HALF_UP);
                }
            }
        } catch (Exception e) {
            return null;
        }

        return null;
    }
}

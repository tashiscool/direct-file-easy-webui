package gov.irs.directfile.api.ats;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import gov.irs.directfile.api.ats.model.ATSScenarioData;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/**
 * Utility class for loading ATS scenario data from JSON resource files.
 */
public class ATSScenarioLoader {

    private static final String RESOURCE_PATH = "/ats-scenarios/";
    private static final ObjectMapper objectMapper;

    static {
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
    }

    /**
     * Load a single ATS scenario from a JSON resource file.
     *
     * @param scenarioFileName The JSON file name (e.g., "scenario-1-tara-black.json")
     * @return The loaded ATSScenarioData
     * @throws IOException if the file cannot be read or parsed
     */
    public static ATSScenarioData loadScenario(String scenarioFileName) throws IOException {
        String resourcePath = RESOURCE_PATH + scenarioFileName;
        try (InputStream is = ATSScenarioLoader.class.getResourceAsStream(resourcePath)) {
            if (is == null) {
                throw new IOException("Resource not found: " + resourcePath);
            }
            return objectMapper.readValue(is, ATSScenarioData.class);
        }
    }

    /**
     * Load all available ATS scenarios.
     *
     * @return List of all loaded scenarios
     */
    public static List<ATSScenarioData> loadAllScenarios() {
        List<ATSScenarioData> scenarios = new ArrayList<>();
        String[] scenarioFiles = {
            "scenario-1-tara-black.json",
            "scenario-2-jones.json",
            "scenario-3-heather.json",
            "scenario-4-smith.json",
            "scenario-5-barker.json",
            "scenario-6-torres.json",
            "scenario-7-boone.json",
            "scenario-8-lewis.json",
            "scenario-12-gardenia.json",
            "scenario-13-birch.json",
            "scenario-nr1-leblanc.json",
            "scenario-nr2-desilva.json",
            "scenario-nr3-alfaro.json",
            "scenario-nr4-hill.json",
            "scenario-nr5-chen.json",
            "scenario-nr12-harrier.json"
        };

        for (String file : scenarioFiles) {
            try {
                scenarios.add(loadScenario(file));
            } catch (IOException e) {
                System.err.println("Warning: Could not load scenario file: " + file + " - " + e.getMessage());
            }
        }

        return scenarios;
    }

    /**
     * Get the ObjectMapper configured for ATS scenario parsing.
     */
    public static ObjectMapper getObjectMapper() {
        return objectMapper;
    }
}

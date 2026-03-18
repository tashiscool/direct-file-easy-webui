package gov.irs.directfile.api.ats;

import static org.junit.jupiter.api.Assertions.assertNotNull;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;

import gov.irs.directfile.api.loaders.domain.TaxDictionaryDigest;
import gov.irs.directfile.api.loaders.processor.FactGraphLoader;
import gov.irs.directfile.api.loaders.processor.XmlProcessor;

class FactDictionarySubsetLoadTest {
    private static final Path TAX_DIR = Path.of("src/main/resources/tax");

    @Test
    void loadsSelectedFactDictionaryModules() throws Exception {
        String rawModules = System.getProperty("subset.modules", "").trim();
        List<String> modules = rawModules.isEmpty()
                ? Files.list(TAX_DIR)
                        .filter(path -> path.getFileName().toString().endsWith(".xml"))
                        .map(path -> path.getFileName().toString().replaceFirst("\\.xml$", ""))
                        .sorted()
                        .collect(Collectors.toList())
                : Arrays.stream(rawModules.split(","))
                        .map(String::trim)
                        .filter(module -> !module.isEmpty())
                        .distinct()
                        .sorted()
                        .collect(Collectors.toList());

        Resource[] resources = modules.stream()
                .map(module -> TAX_DIR.resolve(module + ".xml"))
                .map(FileSystemResource::new)
                .toArray(Resource[]::new);

        TaxDictionaryDigest digest = new XmlProcessor().process(
                "subset:" + String.join(",", modules),
                resources);

        assertNotNull(digest);
        assertNotNull(new FactGraphLoader().createFactDictionary(digest));
    }
}

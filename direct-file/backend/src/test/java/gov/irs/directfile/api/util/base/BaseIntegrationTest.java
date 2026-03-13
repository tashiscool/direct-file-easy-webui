package gov.irs.directfile.api.util.base;

import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.ResultSet;
import java.sql.SQLException;
import javax.sql.DataSource;

import liquibase.Contexts;
import liquibase.LabelExpression;
import liquibase.Liquibase;
import liquibase.database.Database;
import liquibase.database.DatabaseFactory;
import liquibase.database.jvm.JdbcConnection;
import liquibase.exception.LiquibaseException;
import liquibase.resource.ClassLoaderResourceAccessor;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.test.web.servlet.MockMvc;

import gov.irs.directfile.api.taxreturn.TaxReturnRepository;
import gov.irs.directfile.api.user.UserRepository;
import gov.irs.directfile.api.user.models.User;
import gov.irs.directfile.api.util.SecurityTestConfiguration;
import gov.irs.directfile.api.util.TestDataFactory;

@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
public abstract class BaseIntegrationTest extends BaseControllerTest {
    @Autowired
    public MockMvc mvc;

    @Autowired
    public TaxReturnRepository taxReturnRepository;

    @Autowired
    public UserRepository userRepository;

    @Autowired
    public TestDataFactory testDataFactory;

    @Autowired
    public DataSource dataSource;

    @BeforeEach
    void createUsers() {
        ensureSchemaReady();
        for (SecurityTestConfiguration.TestUserProperties testUserProperties :
                SecurityTestConfiguration.testUserMap.values()) {
            User user = testDataFactory.createUserFromTestUser(testUserProperties);
            testUserProperties.setInternalId(user.getId());
        }
    }

    @AfterEach
    public void resetDb() {
        userRepository.deleteAll();
        taxReturnRepository.deleteAll();
    }

    private void ensureSchemaReady() {
        try (Connection connection = dataSource.getConnection()) {
            if (tableExists(connection.getMetaData(), "users")) {
                return;
            }
        } catch (SQLException e) {
            throw new IllegalStateException("Unable to inspect test database metadata", e);
        }

        try (Connection connection = dataSource.getConnection()) {
            Database database =
                    DatabaseFactory.getInstance().findCorrectDatabaseImplementation(new JdbcConnection(connection));
            Liquibase liquibase = new Liquibase("db/changelog.yaml", new ClassLoaderResourceAccessor(), database);
            liquibase.update(new Contexts(), new LabelExpression());
        } catch (SQLException | LiquibaseException e) {
            throw new IllegalStateException("Unable to initialize test database schema", e);
        }
    }

    private boolean tableExists(DatabaseMetaData metadata, String tableName) throws SQLException {
        try (ResultSet tables = metadata.getTables(null, null, tableName, null)) {
            if (tables.next()) {
                return true;
            }
        }
        try (ResultSet tables = metadata.getTables(null, null, tableName.toUpperCase(), null)) {
            return tables.next();
        }
    }
}

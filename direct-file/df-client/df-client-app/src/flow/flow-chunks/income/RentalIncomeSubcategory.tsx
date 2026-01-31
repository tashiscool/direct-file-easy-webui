/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Heading,
  InfoDisplay,
  SaveAndOrContinueButton,
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Rental Income Subcategory
 * Handles Schedule E rental and royalty income reporting
 */
export const RentalIncomeSubcategory = (
  <Subcategory
    route='rental-income'
    completeIf='/scheduleEIsDone'
    dataItems={[
      {
        itemKey: `rentalIncome`,
        conditions: [`/hasRentalIncome`],
      },
      {
        itemKey: `noRentalIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasRentalIncome` }],
      },
    ]}
  >
    <SubSubcategory route='rental-intro'>
      <Screen route='rental-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/rental' />
        <Heading
          i18nKey='/heading/income/rental/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/rental/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/rental/description' />
        <DFModal i18nKey='/info/income/rental/what-counts' />
        <Boolean path='/hasRentalIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasRentalIncome'>
      <Screen route='rental-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/rental' />
        <InfoDisplay i18nKey='/info/knockout/rental/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

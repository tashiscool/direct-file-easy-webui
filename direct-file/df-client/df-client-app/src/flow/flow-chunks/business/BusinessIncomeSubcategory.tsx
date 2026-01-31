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
 * Business Income Subcategory
 * Handles various business income types beyond Schedule C
 * (Schedule C is handled in SelfEmploymentIncomeSubcategory)
 */
export const BusinessIncomeSubcategory = (
  <Subcategory
    route='business-income'
    completeIf='/businessIncomeIsDone'
    dataItems={[
      {
        itemKey: `hasBusinessIncome`,
        conditions: [`/hasBusinessIncome`],
      },
      {
        itemKey: `noBusinessIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasBusinessIncome` }],
      },
    ]}
  >
    <SubSubcategory route='business-intro'>
      <Screen route='business-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/business/income' />
        <Heading
          i18nKey='/heading/business/income/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/business/income/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/business/income/description' />
        <DFModal i18nKey='/info/business/income/types' />
        <Boolean path='/hasBusinessIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasBusinessIncome'>
      <Screen route='business-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/business-income' />
        <InfoDisplay i18nKey='/info/knockout/business-income/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

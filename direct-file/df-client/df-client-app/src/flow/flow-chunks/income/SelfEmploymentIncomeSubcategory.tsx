/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Dollar,
  Heading,
  InfoDisplay,
  LimitingString,
  SaveAndOrContinueButton,
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Self-Employment Income Subcategory
 * Handles Schedule C self-employment business income reporting
 */
export const SelfEmploymentIncomeSubcategory = (
  <Subcategory
    route='self-employment'
    completeIf='/scheduleCIsDone'
    dataItems={[
      {
        itemKey: `selfEmploymentIncome`,
        conditions: [`/hasSelfEmploymentIncome`],
      },
      {
        itemKey: `noSelfEmploymentIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasSelfEmploymentIncome` }],
      },
    ]}
  >
    <SubSubcategory route='self-employment-intro'>
      <Screen route='self-employment-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/self-employment' />
        <Heading
          i18nKey='/heading/income/self-employment/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/self-employment/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/self-employment/description' />
        <DFModal i18nKey='/info/income/self-employment/what-counts' />
        <Boolean path='/hasSelfEmploymentIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasSelfEmploymentIncome'>
      <Screen route='self-employment-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/self-employment' />
        <InfoDisplay i18nKey='/info/knockout/self-employment/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

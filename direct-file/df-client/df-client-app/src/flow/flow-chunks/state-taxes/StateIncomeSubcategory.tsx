/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory, Assertion } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Dollar,
  Heading,
  InfoDisplay,
  SaveAndOrContinueButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * State Income Subcategory
 * Handles state-specific income adjustments and modifications
 */
export const StateIncomeSubcategory = (
  <Subcategory
    route='state-income'
    completeIf='/stateIncomeIsDone'
    displayOnlyIf='/stateFilingRequired'
    dataItems={[
      {
        itemKey: `stateIncomeAdjustments`,
        conditions: [`/hasStateIncomeAdjustments`],
      },
      {
        itemKey: `noStateIncomeAdjustments`,
        conditions: [{ operator: `isFalse`, condition: `/hasStateIncomeAdjustments` }],
      },
    ]}
  >
    <SubSubcategory route='state-income-intro'>
      <Screen route='state-income-adjustments'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/state-taxes/income' />
        <Heading i18nKey='/heading/state-taxes/income/intro' />
        <InfoDisplay i18nKey='/info/state-taxes/income/description' />
        <DFModal i18nKey='/info/state-taxes/income/state-differences' />
        <DFAlert
          i18nKey='/info/state-taxes/income/federal-agi-used'
          headingLevel='h3'
          type='info'
        />
        <SaveAndOrContinueButton />
      </Screen>
      <Assertion
        type='info'
        i18nKey='dataviews./flow/state-taxes/income.assertions.stateIncomeCalculated'
        condition='/stateIncomeIsDone'
      />
    </SubSubcategory>
  </Subcategory>
);

/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory, Assertion } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Enum,
  Heading,
  InfoDisplay,
  SaveAndOrContinueButton,
  DFAlert,
  StateInfoCard,
} from '../../ContentDeclarations.js';

/**
 * State Selection Subcategory
 * Handles state of residence selection and state tax filing determination
 */
export const StateSelectionSubcategory = (
  <Subcategory
    route='state-selection'
    completeIf='/stateSelectionIsDone'
    dataItems={[
      {
        itemKey: `stateSelected`,
        conditions: [`/stateOfResidenceSelected`],
      },
    ]}
  >
    <SubSubcategory route='state-intro'>
      <Screen route='state-residence'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/state-taxes/selection' />
        <Heading i18nKey='/heading/state-taxes/selection/intro' />
        <InfoDisplay i18nKey='/info/state-taxes/selection/description' />
        <DFModal i18nKey='/info/state-taxes/selection/how-to-determine' />
        <Enum path='/stateOfResidence' renderAs='select' />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/stateOfResidenceSelected'>
        <Screen route='state-filing-info' condition='/stateFilingRequired'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/state-taxes/selection' />
          <Heading i18nKey='/heading/state-taxes/selection/filing-required' />
          <StateInfoCard i18nKey='/info/state-taxes/selection/state-card' />
          <InfoDisplay i18nKey='/info/state-taxes/selection/state-filing-info' />
          <DFAlert
            i18nKey='/info/state-taxes/selection/separate-filing'
            headingLevel='h3'
            type='info'
          />
          <SaveAndOrContinueButton />
        </Screen>
        <Screen route='no-state-income-tax' condition='/isNoIncomeTaxState'>
          <ContextHeading displayOnlyOn='edit' i18nKey='/heading/state-taxes/selection' />
          <Heading i18nKey='/heading/state-taxes/selection/no-income-tax' />
          <InfoDisplay i18nKey='/info/state-taxes/selection/no-income-tax-description' />
          <DFAlert
            i18nKey='/info/state-taxes/selection/no-filing-needed'
            headingLevel='h3'
            type='success'
          />
          <SaveAndOrContinueButton />
        </Screen>
        <Assertion
          type='info'
          i18nKey='dataviews./flow/state-taxes/selection.assertions.stateSelected'
          condition='/stateOfResidenceSelected'
        />
      </Gate>
    </SubSubcategory>
  </Subcategory>
);

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
 * Partnership Income Subcategory
 * Handles Schedule K-1 partnership and S-corp income reporting
 */
export const PartnershipIncomeSubcategory = (
  <Subcategory
    route='partnership-income'
    completeIf='/scheduleK1IsDone'
    dataItems={[
      {
        itemKey: `partnershipIncome`,
        conditions: [`/hasPartnershipIncome`],
      },
      {
        itemKey: `noPartnershipIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasPartnershipIncome` }],
      },
    ]}
  >
    <SubSubcategory route='partnership-intro'>
      <Screen route='partnership-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/partnership' />
        <Heading
          i18nKey='/heading/income/partnership/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/partnership/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/partnership/description' />
        <DFModal i18nKey='/info/income/partnership/what-is-k1' />
        <Boolean path='/hasPartnershipIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasPartnershipIncome'>
      <Screen route='partnership-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/partnership' />
        <InfoDisplay i18nKey='/info/knockout/partnership/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

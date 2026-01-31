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
 * Foreign Income Subcategory
 * Handles Form 2555 foreign earned income exclusion
 */
export const ForeignIncomeSubcategory = (
  <Subcategory
    route='foreign-income'
    completeIf='/form2555IsDone'
    dataItems={[
      {
        itemKey: `foreignIncome`,
        conditions: [`/hasForeignIncome`],
      },
      {
        itemKey: `noForeignIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasForeignIncome` }],
      },
    ]}
  >
    <SubSubcategory route='foreign-intro'>
      <Screen route='foreign-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/foreign' />
        <Heading
          i18nKey='/heading/income/foreign/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/foreign/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/foreign/description' />
        <DFModal i18nKey='/info/income/foreign/what-counts' />
        <Boolean path='/hasForeignIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasForeignIncome'>
      <Screen route='foreign-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/foreign-income' />
        <InfoDisplay i18nKey='/info/knockout/foreign-income/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

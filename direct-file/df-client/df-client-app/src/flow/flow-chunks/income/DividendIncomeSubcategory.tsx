/* eslint-disable max-len */
import { Gate, Screen, Subcategory, SubSubcategory } from '../../flowDeclarations.js';
import {
  Boolean,
  ContextHeading,
  DFModal,
  Dollar,
  Heading,
  InfoDisplay,
  SaveAndOrContinueButton,
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Dividend Income Subcategory
 * Handles Form 1099-DIV dividend income reporting
 */
export const DividendIncomeSubcategory = (
  <Subcategory
    route='dividends'
    completeIf='/form1099DivIsDone'
    dataItems={[
      {
        itemKey: `dividendIncome`,
        conditions: [`/hasDividendIncome`],
      },
      {
        itemKey: `noDividendIncome`,
        conditions: [{ operator: `isFalse`, condition: `/hasDividendIncome` }],
      },
    ]}
  >
    <SubSubcategory route='dividend-intro'>
      <Screen route='dividend-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/dividends' />
        <Heading
          i18nKey='/heading/income/dividends/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/dividends/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/dividends/description' />
        <DFModal i18nKey='/info/income/dividends/what-counts' />
        <Boolean path='/hasDividendIncome' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasDividendIncome'>
      <Screen route='dividend-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/dividends' />
        <InfoDisplay i18nKey='/info/knockout/dividends/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

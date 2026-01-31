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
 * Capital Gains Subcategory
 * Handles Schedule D capital gains and losses reporting
 */
export const CapitalGainsSubcategory = (
  <Subcategory
    route='capital-gains'
    completeIf='/scheduleDIsDone'
    dataItems={[
      {
        itemKey: `capitalGains`,
        conditions: [`/hasCapitalGains`],
      },
      {
        itemKey: `noCapitalGains`,
        conditions: [{ operator: `isFalse`, condition: `/hasCapitalGains` }],
      },
    ]}
  >
    <SubSubcategory route='capital-gains-intro'>
      <Screen route='capital-gains-has-income'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/income/capital-gains' />
        <Heading
          i18nKey='/heading/income/capital-gains/intro'
          condition={{ operator: `isFalse`, condition: `/isFilingStatusMFJ` }}
        />
        <Heading i18nKey='/heading/income/capital-gains/intro-mfj' condition='/isFilingStatusMFJ' />
        <InfoDisplay i18nKey='/info/income/capital-gains/description' />
        <DFModal i18nKey='/info/income/capital-gains/what-counts' />
        <Boolean path='/hasCapitalGains' />
        <SaveAndOrContinueButton />
      </Screen>
    </SubSubcategory>
    <Gate condition='/hasCapitalGains'>
      <Screen route='capital-gains-ko' isKnockout={true}>
        <IconDisplay name='ErrorOutline' size={9} isCentered />
        <Heading i18nKey='/heading/knockout/capital-gains' />
        <InfoDisplay i18nKey='/info/knockout/capital-gains/description' />
        <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
        <KnockoutButton i18nKey='button.knockout' />
      </Screen>
    </Gate>
  </Subcategory>
);

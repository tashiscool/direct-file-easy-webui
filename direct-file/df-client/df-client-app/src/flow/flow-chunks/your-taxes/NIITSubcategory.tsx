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
  IconDisplay,
  KnockoutButton,
  DFAlert,
} from '../../ContentDeclarations.js';

/**
 * Net Investment Income Tax (NIIT) Subcategory
 * Handles Form 8960 NIIT calculations (3.8% tax on investment income)
 */
export const NIITSubcategory = (
  <Subcategory
    route='niit'
    completeIf='/form8960IsDone'
    dataItems={[
      {
        itemKey: `niitApplies`,
        conditions: [`/niitApplies`],
      },
      {
        itemKey: `noNiit`,
        conditions: [{ operator: `isFalse`, condition: `/niitApplies` }],
      },
    ]}
  >
    <SubSubcategory route='niit-check'>
      <Screen route='niit-intro'>
        <ContextHeading displayOnlyOn='edit' i18nKey='/heading/your-taxes/niit' />
        <Heading i18nKey='/heading/your-taxes/niit/intro' />
        <InfoDisplay i18nKey='/info/your-taxes/niit/description' />
        <DFModal i18nKey='/info/your-taxes/niit/who-pays' />
        <DFAlert
          i18nKey='/info/your-taxes/niit/auto-calculated'
          headingLevel='h3'
          type='info'
        />
        <SaveAndOrContinueButton />
      </Screen>
      <Gate condition='/niitApplies'>
        <Screen route='niit-ko' isKnockout={true}>
          <IconDisplay name='ErrorOutline' size={9} isCentered />
          <Heading i18nKey='/heading/knockout/niit' />
          <InfoDisplay i18nKey='/info/knockout/niit/description' />
          <DFAlert i18nKey='/info/knockout/generic-other-ways-to-file' headingLevel='h2' type='warning' />
          <KnockoutButton i18nKey='button.knockout' />
        </Screen>
      </Gate>
      <Assertion
        type='info'
        i18nKey='dataviews./flow/your-taxes/niit.assertions.noNiitRequired'
        condition={{ operator: `isFalse`, condition: `/niitApplies` }}
      />
    </SubSubcategory>
  </Subcategory>
);
